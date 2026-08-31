Camera_rtsp_global_links = {1: {'ANPR': 'rtsp://admin:abcd2024@115.245.147.34:1111/enr/live/1/1', 'ANPRId': 10, 
                                'Top': 'rtsp://admin:abcd2024@115.245.147.34:1112/enr/live/1/1', 'TopId': 11}, 
                            2: {'ANPR': 'rtsp://admin:abcd2024@115.245.147.34:1121/enr/live/1/1', 'ANPRId': 12, 
                                'Top': 'rtsp://admin:abcd2024@115.245.147.34:1122/enr/live/1/1', 'TopId': 134},
                            3: {'ANPR': 'rtsp://admin:abcd2024@115.245.147.34:1151/enr/live/1/1', 'ANPRId': 12, 
                            'Top': 'rtsp://admin:abcd2024@115.245.147.34:1152/enr/live/1/1', 'TopId': 134},
                            4: {'ANPR': 'rtsp://admin:abcd2024@115.245.147.34:1161/enr/live/1/1', 'ANPRId': 12, 
                                'Top': 'rtsp://admin:abcd2024@115.245.147.34:1162/enr/live/1/1', 'TopId': 134}
                            
                                }

Camera_rtsp_local_links = {1: {'ANPR': 'rtsp://admin:abcd2024@192.168.1.11:554/enr/live/1/1', 'ANPRId': 10, 
                               'Top': 'rtsp://admin:abcd2024@192.168.1.12:554/enr/live/1/1', 'TopId': 11}, 
                            2: {'ANPR': 'rtsp://admin:abcd2024@192.168.1.21:554/enr/live/1/1', 'ANPRId': 12, 
                                'Top': 'rtsp://admin:abcd2024@192.168.1.22:554/enr/live/1/1', 'TopId': 134},
                            3: {'ANPR': 'rtsp://admin:abcd2024@192.168.1.51:554/enr/live/1/1', 'ANPRId': 12, 
                                'Top': 'rtsp://admin:abcd2024@192.168.1.52:554/enr/live/1/1', 'TopId': 134},
                            4: {'ANPR': 'rtsp://admin:abcd2024@192.168.1.61:554/enr/live/1/1', 'ANPRId': 12, 
                                'Top': 'rtsp://admin:abcd2024@192.168.1.62:554/enr/live/1/1', 'TopId': 134},
                            
                                }
RFID_ip_ports = {1: {'server_ip': '192.168.1.13', 'server_port': 1510}, 
                 2: {'server_ip': '192.168.1.23', 'server_port': 1520},
                 3: {'server_ip': '192.168.1.53', 'server_port': 1530},
                 4: {'server_ip': '192.168.1.63', 'server_port': 1540},
                 
                 }

"""
Location : Neelbad Bhopal

Static IP : 115.245.147.34
Server IP : 192.168.1.2
NVR1 IP : 192.168.1.41   pass : abcd@1234
NVR2 IP : 192.168.1.42   pass : abcd@1234


Local Links:

Lane 1 (Bhopal to Neelbad)

ANPR
Norden(eyenor)_box(ANPR)1 : rtsp://admin:abcd2024@192.168.1.11:554/enr/live/1/1

TOP

Norden(eyenor)_top1 : rtsp://admin:abcd2024@192.168.1.12:554/enr/live/1/1

RFID : 192.168.1.13 
Reader_port : 60000   
Listening_port : 1510  
 
Lane 2 (Bhopal to Neelbad)

ANPR

Norden(eyenor)_box(ANPR)2 : rtsp://admin:abcd2024@192.168.1.21:554/enr/live/1/1

Top

Norden(eyenor)_top2 : rtsp://admin:abcd2024@192.168.1.22:554/enr/live/1/1

RFID : 192.168.1.23 
Reader_port : 60000   
Listening_port : 1520

Lane 3 (Neelbad to Bhopal)

ANPR
Norden(eyenor)_box(ANPR)1 : rtsp://admin:abcd2024@192.168.1.51:554/enr/live/1/1

TOP

Norden(eyenor)_top1 : rtsp://admin:abcd2024@192.168.1.52:554/enr/live/1/1

RFID : 192.168.1.53 
Reader_port : 60000   
Listening_port : 1530  
 
Lane 4 (Neelbad to Bhopal)

ANPR

Norden(eyenor)_box(ANPR)2 : rtsp://admin:abcd2024@192.168.1.61:554/enr/live/1/1

Top

Norden(eyenor)_top2 : rtsp://admin:abcd2024@192.168.1.62:554/enr/live/1/1

RFID : 192.168.1.63 
Reader_port : 60000   
Listening_port : 1540

junction_box : rtsp://admin:abcd@1234@192.168.1.31:554/Streaming/Channels/101

Surveillance_camera gantry

Hikvision_top_camera : rtsp://admin:abcd@1234@192.168.1.32:554/Streaming/Channels/101


Global Links:

Lane 1

ANPR
Norden(eyenor)_box(ANPR)1 : rtsp://admin:abcd2024@115.245.147.34:1111/enr/live/1/1

TOP

Norden(eyenor)_top1 : rtsp://admin:abcd2024@115.245.147.34:1112/enr/live/1/1

RFID : 192.168.1.13 
Reader_port : 60000   
Listening_port : 1510  
 
Lane 2

ANPR

Norden(eyenor)_box(ANPR)2 : rtsp://admin:abcd2024@115.245.147.34:1121/enr/live/1/1

Top

Norden(eyenor)_top2 : rtsp://admin:abcd2024@115.245.147.34:1122/enr/live/1/1

RFID : 192.168.1.23 
Reader_port : 60000   
Listening_port : 1520

Lane 3

ANPR
Norden(eyenor)_box(ANPR)1 : rtsp://admin:abcd2024@115.245.147.34:1151/enr/live/1/1

TOP

Norden(eyenor)_top1 : rtsp://admin:abcd2024@115.245.147.34:1152/enr/live/1/1

RFID : 192.168.1.53 
Reader_port : 60000   
Listening_port : 1530  
 
Lane 4

ANPR

Norden(eyenor)_box(ANPR)2 : rtsp://admin:abcd2024@115.245.147.34:1161/enr/live/1/1

Top

Norden(eyenor)_top2 : rtsp://admin:abcd2024@115.245.147.34:1162/enr/live/1/1

RFID : 192.168.1.63 
Reader_port : 60000   
Listening_port : 1540


junction_box : rtsp://admin:abcd@1234@115.245.147.34:1131/Streaming/Channels/101

Surveillance_camera gantry

Hikvision_top_camera : rtsp://admin:abcd@1234@115.245.147.34:1132/Streaming/Channels/101
"""