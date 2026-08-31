import serial
import time
from datetime import datetime

# Replace 'COM3' with the appropriate serial port for your system
# For Linux or Mac, it might be something like '/dev/ttyACM0' or '/dev/ttyUSB0'
arduino_port = '/dev/ttyACM0'
baud_rate = 9600

def is_night_time():
    """Returns True if the current time is between 6 PM and 6 AM, otherwise False."""
    now = datetime.now()
    current_hour = now.hour
    return current_hour >= 18 or current_hour < 7

def control_relay(command):
    """Send a command to the Arduino to control the relay."""
    try:
        # Open the serial port
        ser = serial.Serial(arduino_port, baud_rate)
        time.sleep(2)  # Wait for the connection to establish

        # Send the command to the Arduino
        ser.write(command.encode())
        print(f"Command '{command}' sent to Arduino")

        # Close the serial port
        ser.close()
    except serial.SerialException as e:
        print("Serial port error:", e)
    except Exception as e:
        print("Error:", e)

if is_night_time():
    # Send the command to turn the relay on if it's night time
    control_relay('1')
    # control_relay('2')
    print("Relay turned ON, Light turned ON")
else:
    # Send the command to turn the relay off if it's not night time
    control_relay('0')
    # control_relay('3')
    print("It is not between 6 PM and 6 AM, Light remains OFF")
