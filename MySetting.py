#_______________________________________you can set the switch and port information here_______________
#######################################
        #sw_type[sw_no][]
        #  otn wave
        #   ||  ||
        # " 0   0" 
        #[0,0]=IP ,[1,0]=OTN, [0,1] = WAVE, [1,1] = OTN & WAVE
#######################################

sw_type = {	1:[1,0],
			2:[0,0],
			3:[1,0],
			4:[1,0]
			}
 
#######################################
#		features[sw_no][port_no][]
#		features[0,	 	 1,    2,   3,    4,    5,   6,    7,   8,    9,      10,              11,                        12,                13,                 14    ]   
#		 [		FIBER,  WAVE, OTN, SDH, SONET, ETH, VLAN, MPLS, IP, TCP/UDP, SUPP_SW_GRAM, sup_sdh_port_bandwidth, sup_otn_port_bandwidth, peer_port_no,  peer_datapath_id]
#######################################

features = {
			1:{	1: [0,0,0,0,0,0,0,0,1,0,0,0,0,2,3],
				2: [0,0,0,0,0,0,0,0,1,0,0,0,0,3,4],
				3: [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
				4: [1,1,1,1,1,1,1,0,0,0,0,0,0,0,0],
				65534: [1,0,1,0,1,0,1,0,0,0,1,100,100,100,100]
			},#switch 0

	 		2:{	1: [0,1,0,0,0,0,0,0,0,0,10,0,0,3,3],
	 			2: [0,1,0,0,0,0,0,0,0,0,10,0,0,2,4],
	 			3: [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
				4: [1,1,0,0,1,0,1,0,0,1,18,81,81,18,91],
				65534: [1,1,1,1,1,1,1,1,0,1,1,101,111,11,11]
			},#switch 1

	 		3:{	1: [0,0,0,0,0,0,0,0,1,0,0,0,0,0,0],
	 			2: [0,0,0,0,0,0,0,0,1,0,0,0,0,1,1],
	 			3: [0,1,0,0,0,0,0,0,0,0,10,0,0,1,2],
	 		 	4: [1,1,0,0,1,0,1,0,1,0,0,0,0,0,0],
	 		 	65534: [1,0,1,0,1,0,1,0,1,0,1,1,1,1,1]
	 		},#switch 2

	 		4:{	1: [0,0,0,0,0,0,0,0,1,0,0,0,0,0,0],
	 			2: [0,1,0,0,0,0,0,0,0,0,10,0,0,2,2],
	 			3: [0,0,0,0,0,0,0,0,1,0,0,0,0,2,1],
	 		 	4: [1,0,0,0,1,0,1,0,1,1,1,1,1,1,1],
	 		 	65534: [1,0,1,0,0,0,0,0,0,1,0,1,0,1,1]
	 		} #switch 3
	 	}
#######################################
#		f_wave[sw_no][port_no][]
# 		[1,                      2,  				3  ]
#  		center_freq_lmda     num_lmda     freq_space_lmda
#######################################
f_wave = {
			1:{	1:[0,0,0],
				2:[0,0,0],
				3:[0,0,0],
				4:[0,0,0],
				65534:[0,0,0]},#sw_wave
			2:{	1:[192,10,50],
				2:[192,10,50],
				3:[0,0,0],
				4:[0,0,0],
				65534:[0,0,0]},
			3:{	1:[0,0,0],
				2:[0,0,0],
				3:[192,10,50],
				4:[0,0,0],
				65534:[0,0,0]},
			4:{	1:[0,0,0],
				2:[192,10,50],
				3:[0,0,0],
				4:[0,0,0],
				65534:[0,0,0]}
		} 
#_______________________________________________________________________________________________________

if __name__ == '__main__':
	print features[1][1][0]