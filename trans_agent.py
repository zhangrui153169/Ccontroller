"""
In this agent, the Tornado TCP server will use one process to manage all the classes.
Therefore, the total throughput of this script will be affected.  
"""
import errno
import functools
import tornado.ioloop as ioloop
import socket
import libopenflow as of
import libopencflow as ofc
import convert

import Queue

#create a connection between socket fd of (controller, sw) and sw class 
fdmap = {}
num = 0

"""
Print connection information
"""
def print_connection(connection, address):
        print "connection:", connection, address

"""
Create a new socket
The parameter ``block`` determine if the return socket is blocking
or nonblocking socket. Use '1' when creating a socket which connect
a controller.
"""
def new_sock(block):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setblocking(block)
    return sock

"""
The switch class maintains the connection between controller and individual 
switches. For each OpenFlow switch, this transparent agent create a object of this 
class. 
"""
class switch():
    def __init__(self, sock_sw, sock_con):
        self.sock_sw    = sock_sw
        self.sock_con   = sock_con
        self.fd_sw      = sock_sw.fileno()
        self.fd_con     = sock_con.fileno()
        self.queue_con  = Queue.Queue()
        self.queue_sw   = Queue.Queue()
        self.buffer     = {}
        self.counter    = 0
        self.dpid       = 0
        
    def controller_handler(self, address, fd, events):
        if events & io_loop.READ:
            data = self.sock_con.recv(1024)
            if data == '':
                print "controller disconnected"
                io_loop.remove_handler(self.fd_con)
                print "closing connection to switch"
                self.sock_sw.close()
                io_loop.remove_handler(self.fd_sw)
            else:
                rmsg = of.ofp_header(data[0:8])
                # Here, we can manipulate OpenFlow packets from CONTROLLER.
                #rmsg.show()
                if rmsg.type == 14:  #cflow_mod   #firstly,we split the packet.
                    header = ofc.ofp_header(data[0:8])
                    print "ofc_xid = ", header.xid
                    cflow_mod = ofc.ofp_cflow_mod(data[8:16])
                    cflow_connect_wildcards = ofc.ofp_connect_wildcards(data[16:18])
                    cflow_connect = ofc.ofp_connect(data[18:92])
                    actions = data[92:]
                    msg = header/cflow_mod/cflow_connect_wildcards/cflow_connect  
                    data = convert.ofc2of(msg, self.buffer, self.dpid) #sencondly,we rebuilt the packet.
                    print "flow_mod_msg xid:", header.xid
                    #data.show()
                #if rmsg.type == 6: #OFPT_FEATURES_REPLY 
                   # header = ofc.ofp_header(data[0:8])
                   # print "ofc_xid = ", header.xid
                   # cflow_mod = ofc.ofp_cflow_mod(data[8:16])
                   # cflow_connect_wildcards = ofc.ofp_connect_wildcards(data[16:18])
                   # cflow_connect = ofc.ofp_connect(data[18:92])
                    #actions = data[92:]
                    #msg = header/cflow_mod/cflow_connect_wildcards/cflow_connect
                    #data = convert.ofc2of(msg, self.buffer, self.dpid)
                    #print "flow_mod_msg xid:", header.xid

                io_loop.update_handler(self.fd_sw, io_loop.WRITE)
                self.queue_sw.put(str(data))#put it into the queue of packet which need to send to Switch.  
    
        if events & io_loop.WRITE:
            #print "trying to send packet to controller" 
            try:
                next_msg = self.queue_con.get_nowait()
            except Queue.Empty:
                #print "%s queue empty" % str(address)
                io_loop.update_handler(self.fd_con, io_loop.READ)
            else:
                #print 'sending "%s" to %s' % (of.ofp_type[of.ofp_header(next_msg).type], self.sock_con.getpeername())
                self.sock_con.send(next_msg)

    def switch_handler(self, address, fd, events):
        if events & io_loop.READ:
            data = self.sock_sw.recv(1024)
            if data == '':
                print "switch disconnected"
                io_loop.remove_handler(self.fd_sw)
                print "closing connection to controller"
                self.sock_con.close()
                io_loop.remove_handler(self.fd_con)
            else:
                rmsg = of.ofp_header(data[0:8])
                #rmsg.show()
                if rmsg.type == 6:
                    print "OFPT_FEATURES_REPLY"                                                  #Actually,we just need to change here.
                    print "rmsg.load:",len(body)/48
                    header = ofc.header(data[0:8]) 
                    print "ofp_features_reply.xid ", header.xid
                    msg = of.ofp_features_reply(data[8:32])#length of reply msg      corretly!
                    msg_port = of.ofp_features_reply(data[32:])
                    msg = header/msg/msg_port                      #we calculate the number of the ports in convert.
                    self.dpid=msg.datapath_id

                    data = convert.ofc2of(msg, self.buffer, self.dpid)   #we use the covert's of2ofc function to finish the transfer. 
                    #self.dpid=msg.datapath_id
                    io_loop.update_handler(self.fd_sw, io_loop.WRITE)
                    self.queue_con.put(str(data))#put it into the queue of packet which need to send to controller.  
      
                elif rmsg.type == 10:
                    #print "Packet In"
                    pkt_in_msg = of.ofp_packet_in(data[8:18])
                    #pkt_in_msg.show()
                    pkt_parsed = of.Ether(data[18:])
                    #pkt_parsed.show()
                    #[port + id] --> [buffer_id + pkt_in_msg]
                    self.counter+=1
                    if isinstance(pkt_parsed.payload, of.IP) or isinstance(pkt_parsed.payload.payload, of.IP):
                        if isinstance(pkt_parsed.payload.payload, of.ICMP):
                            self.buffer[(pkt_in_msg.in_port, self.counter)] = [pkt_in_msg.buffer_id, rmsg/pkt_in_msg/pkt_parsed] # bind buffer id with in port 
                            #print "ping", self.buffer  
                        elif isinstance(pkt_parsed.payload.payload.payload, of.ICMP):
                            self.buffer[(pkt_in_msg.in_port, self.counter)] = [pkt_in_msg.buffer_id, rmsg/pkt_in_msg/pkt_parsed] # bind buffer id with in port 
                            #print "ping", self.buffer
                            
                    #change the xid in header, so that the agent can track the packet/buffer_id more precisely
                    rmsg.xid = self.counter
                    data = rmsg/pkt_in_msg/pkt_parsed
                    #print "pkt_in_msg xid:", self.counter, pkt_in_msg.buffer_id
                    #rmsg.show()
                # Here, we can manipulate OpenFlow packets from SWITCH.


                io_loop.update_handler(self.fd_con, io_loop.WRITE)
                self.queue_con.put(str(data))
    
        if events & io_loop.WRITE:
            try:
                next_msg = self.queue_sw.get_nowait()
            except Queue.Empty:
                #print "%s queue empty" % str(address)
                io_loop.update_handler(self.fd_sw, io_loop.READ)
            else:
                #print 'sending "%s" to %s' % (of.ofp_type[of.ofp_header(next_msg).type], self.sock_sw.getpeername())
                self.sock_sw.send(next_msg)

"""
For the callback function of socket listening, the agent function will first
try to accept the connection started by switch. And if the connection is successful,
this function will continue on creating another socket to connect the controller.
If the controller cannot be reached, there will be ``ECONNREFUSED`` error. 

After all these things are done, we will have two sockets, one from OpenFlow switch, another 
one to controller. Send these two sockets as parameter, a new switch object can be 
created. Before exit the agent function, this function will add ``new_switch.switch_handler``
and ``new_switch.controller_handler`` to callback function of their own socket.
"""
def agent(sock, fd, events):
    #TODO: create a new class for switches. when a switch connected to agent, new class
    #also, the sw is connected to controller using another socket.
    #print fd, sock, events
    
    #1. accept connection from switch
    try:
        connection, address = sock.accept()
    except socket.error, e:
        if e.args[0] not in (errno.EWOULDBLOCK, errno.EAGAIN):
            raise
        return
    connection.setblocking(0)
    
    #2. connecting to controller
    #no idea why, but when not blocking, it says: error: [Errno 36] Operation now in progress
    sock_control = new_sock(1)
    try:
        sock_control.connect(("localhost",6634))#controller's IP, better change it into an argument
    except socket.error, e:
        if e.args[0] not in (errno.ECONNREFUSED, errno.EINPROGRESS):
            raise
        if e.args[0] == errno.ECONNREFUSED:
            print "cannot establish connection to controller, please check your config."
        return
    sock_control.setblocking(0)
    
    #3. create sw class object
    global num
    num = num + 1
    new_switch = switch(connection, sock_control)
    print "switch instance No.", num
    fdmap[connection.fileno()] = new_switch
    fdmap[sock_control.fileno()] = new_switch
    
    #print_connection(connection, address)
    #print_connection(sock_control, sock_control.getpeername())
    controller_handler = functools.partial(new_switch.controller_handler, address)
    io_loop.add_handler(sock_control.fileno(), controller_handler, io_loop.READ)
    print "agent: connected to controller"
    
    switch_handler = functools.partial(new_switch.switch_handler, address)
    io_loop.add_handler(connection.fileno(), switch_handler, io_loop.READ)
    print "agent: connected to switch", num

if __name__ == '__main__':
    """
    For Tornado, there usually is only one thread, listening to the socket
    below. And also, this code block uses ``ioloop.add_handler()`` function
    to register a callback function if ``ioloop.READ`` event happens.
    
    When a new request from of switch, it will trigger ``ioloop.READ`` event
    in Tornado. And Tornado will execute the callback function ``agent()``.
    """
    sock = new_sock(0)
    sock.bind(("", 6633))
    sock.listen(6633)
    num = 0
    io_loop = ioloop.IOLoop.instance()
    callback = functools.partial(agent, sock)
    print sock, sock.getsockname()
    io_loop.add_handler(sock.fileno(), callback, io_loop.READ)
    io_loop.start()