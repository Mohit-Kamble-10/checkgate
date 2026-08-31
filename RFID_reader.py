import socket
import binascii
import datetime
import time 
from configs import config 
# from configs import camera_config
import sys
import os 
import json
import shutil
import logging
lane_no=sys.argv[1] # string 1,2,3 lane no 

now = datetime.datetime.now()
start_script_datetime=now.strftime("%d_%m_%Y_%H_%M")

Current_log_path=config.root_path+f"/logs/RFID_Reader_Logs_{str(lane_no)}.log"
backup_logs_path=config.root_path+f"/logs/RFID_Reader_Logs/"
os.makedirs(backup_logs_path,exist_ok=True)
if os.path.exists(Current_log_path):
    shutil.move(Current_log_path,backup_logs_path+f"RFID_Reader_Logs_{str(lane_no)}_{start_script_datetime}.log")

FORMAT = "%(asctime)s: %(filename)s: %(levelname)s :%(lineno)5s:: - %(funcName)10s() :  %(message)s"
logging.basicConfig(filename=Current_log_path,
                    format=FORMAT,
                    filemode='a',
                    level=logging.DEBUG, # Set logging level
                    force=True)


if os.path.exists(config.master_jsons+'/RFID_details.json'):
    with open(config.master_jsons+'/RFID_details.json') as json_file:
        get_RFID_profile_data = json.load(json_file)
        logging.info(str(get_RFID_profile_data))
    server_ip=get_RFID_profile_data[f'RFID_{str(lane_no)}']['serverIP']
    server_port=int(get_RFID_profile_data[f'RFID_{str(lane_no)}']['receiverPort'])
    rfidPort=int(get_RFID_profile_data[f'RFID_{str(lane_no)}']['rfidPort'])
    logging.info('server_ip : '+str(server_ip))
    logging.info('server_port : '+str(server_port))
    logging.info('rfidPort : '+str(rfidPort))
    
else:
    print('RFID_details.json not found')
    print(config.master_jsons+'/RFID_details.json')
    logging.error('RFID_details.json not found')
    # exit()


# server_ip=camera_config.RFID_ip_ports[int(lane_no)]['server_ip']
# server_port=camera_config.RFID_ip_ports[int(lane_no)]['server_port']
print('server_ip : ',server_ip)
print('server_port : ',server_port)
print('rfidPort : ',rfidPort)
def trim_log_file(file_path, limit=1000):
    """Ensures the log file does not exceed the given number of lines."""
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            lines = file.readlines()
        # print('len(lines)  : ',len(lines) )
        # Trim to last `limit` lines
        if len(lines) > limit:
            lines = lines[-limit:]

        # Rewrite the trimmed data
        with open(file_path, "w") as file:
            file.writelines(lines)
class main():
    def main(self):
        # RFID reader details
        # reader_socket=False
        # server_socket=False
        log_file=False
        
        try:
            # Create a server socket
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((server_ip, server_port))
            server_socket.listen(1)  # Listen for incoming connections
            LOG_LIMIT = 1000  # Keep only the last 100 lines
            print("server_socket : ",server_socket)
            logging.info('server_socket : '+str(server_socket))
            try:
                log_file_path = config.root_path + f"/logs/syrotech_rfid_logs_{str(lane_no)}.txt"
                log_file = open(log_file_path, "a")  # Open a file to append logs

                log_file.write("RFID reader log started at: " + str(datetime.datetime.now()) + "\n")

                print("Waiting for RFID reader to connect...")

                # Accept incoming connection from RFID reader
                reader_socket, reader_addr = server_socket.accept()
                print(f"RFID reader connected from: {reader_addr}")
                start_time=time.time()
                if log_file:
                    while True:
                        # Example command to request RFID data
                        command = b'READ_RFID_DATA\n'
                        reader_socket.send(command)

                        # Receive data from the RFID reader
                        data = reader_socket.recv(1024)
                        hex_data = binascii.hexlify(data).decode('utf-8')
                        now=datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
                        log_message = f"{now}-{hex_data}\n"
                        # print(log_message)
                        # print("----"*20)
                        
                        log_file.write(log_message)
                        
                        log_file.flush()  # Immediately flush the buffer to ensure the log is saved
                        end_time=time.time()
                        if end_time-start_time>10:
                            trim_log_file(log_file_path)
                            start_time=time.time()
                        else:
                            pass
                            # print('waiting : ')

            except Exception as e:
                logging.error(str(e))
                print(e)
        except OSError as e:
            logging.error(str(e))
            if config.check_error:
                print("RFID reader : ",e)
                    
            if e.errno == 98:
                print(f"Port {server_port} is in use, waiting...")
                time.sleep(5)
                
            else:
                print(e)
                raise  # Re-raise exception if it's a different error

        except Exception as e:
            logging.error(str(e))
            error_message = f"Error: {e}\n"
            print("RFID reader error_message : ",error_message)
            log_file.write(error_message)
            if 'Input/output error' in  str(e):
                logging.error('RFID Reader code Error : RFID_reader.py  Restarted')
                os.execv(sys.executable, ['python3'] + sys.argv)
                

        finally:
            # Close the sockets and the log file
            if reader_socket:
                reader_socket.close()
                # del(reader_socket)
                print('reader_socket Close.....')
            if server_socket:
                server_socket.close()
                # del(server_socket)
                
                print('server_socket Close.....')
            if log_file:
                log_file.close()
                # del(log_file)
                print('Log file deleted.....')
            

print('completed')
if __name__ == "__main__":
    main().main()
