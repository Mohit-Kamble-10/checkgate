import subprocess
import serial
import time

# Function to check network availability
def check_network():
    try:
        result = subprocess.run(['ping', '-c', '1', '192.168.1.1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False

# Check network availability
if check_network():
    print('Network available')
else:
    print('Network not available')

    # Replace 'COM3' with the appropriate serial port for your system
    # For Linux or Mac, it might be something like '/dev/ttyACM0' or '/dev/ttyUSB0'
    arduino_port = '/dev/ttyACM0'  # Adjust this to your Arduino's serial port
    baud_rate = 9600

    try:
        # Open the serial port
        ser = serial.Serial(arduino_port, baud_rate, timeout=1)
        time.sleep(2)
        ser.write(b'3') #Power OFF
        time.sleep(5)
        # Send command to Arduino to start execution
        ser.write(b'2')  # Power ON
        print('Router restarted')
        print("Command sent to Arduino")

        # Wait for some time to allow Arduino to execute setup and initial connection
        # time.sleep(2)  # Adjust this according to the time needed for Arduino setup

        # Close the serial port
        ser.close()
        
        print("Serial port closed")

    except serial.SerialException as e:
        print("Serial port error:", e)
    except Exception as e:
        print("Error:", e)
