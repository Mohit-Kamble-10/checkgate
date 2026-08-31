Camera_rtsp_global_links = {1: {'ANPR': 'rtsp://admin:abcd2024@117.250.168.138:1111/enr/live/1/1', 'ANPRId': 10, 
                                'Top': 'rtsp://admin:abcd2024@117.250.168.138:1112/enr/live/1/1', 'TopId': 11}
                            
                                }

Camera_rtsp_local_links = {1: {'ANPR': 'rtsp://admin:abcd2024@192.168.1.11:554/enr/live/1/1', 'ANPRId': 10, 
                               'Top': 'rtsp://admin:abcd2024@192.168.1.12:554/enr/live/1/1', 'TopId': 11}
                            
                                }
RFID_ip_ports = {1: {'server_ip': '192.168.1.13', 'server_port': 1510}
                 
                 }

"""
Location : Eintkhedi Bhopal

Static IP : 117.250.168.138
Server IP : 192.168.1.2
NVR1 IP : 192.168.1.41   pass : abcd2024

Local Links:

Lane 1 (Bhopal to Neelbad)

ANPR
Norden(eyenor)_box(ANPR)1 : rtsp://admin:abcd2024@192.168.1.11:554/enr/live/1/1

TOP

Norden(eyenor)_top1 : rtsp://admin:abcd2024@192.168.1.12:554/enr/live/1/1

RFID : 192.168.1.13 
Reader_port : 60000   
Listening_port : 1510  

TOP surveillance (only for surveillance purpose) vehicle entering in bhopal from 2nd route

Norden(eyenor)_top2 : rtsp://admin:abcd2024@192.168.1.22:554/enr/live/1/1


junction_box : rtsp://admin:abcd2024@192.168.1.31:554/Streaming/Channels/101

Surveillance_camera gantry : rtsp://admin:abcd2024@192.168.1.32:554/Streaming/Channels/101

Global Links:

Lane 1

ANPR
Norden(eyenor)_box(ANPR)1 : rtsp://admin:abcd2024@117.250.168.138:1111/enr/live/1/1

TOP

Norden(eyenor)_top1 : rtsp://admin:abcd2024@117.250.168.138:1112/enr/live/1/1

TOP surveillance (only for surveillance purpose) vehicle entering in bhopal from 2nd route

Norden(eyenor)_top2 : rtsp://admin:abcd2024@117.250.168.138:1122/enr/live/1/1

junction_box : rtsp://admin:abcd2024@117.250.168.138:1131/Streaming/Channels/101

Surveillance_camera gantry : rtsp://admin:abcd2024@117.250.168.138:1132/Streaming/Channels/101

"""