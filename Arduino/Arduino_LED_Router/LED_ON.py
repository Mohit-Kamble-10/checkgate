import serial
import time

# Replace 'COM3' with the appropriate serial port for your system
# For Linux or Mac, it might be something like '/dev/ttyACM0' or '/dev/ttyUSB0'
arduino_port = '/dev/ttyACM0'
baud_rate = 9600

# Open the serial port
ser = serial.Serial(arduino_port, baud_rate)
time.sleep(2)  # Wait for the connection to establish

# Send the command to turn the relay on
ser.write(b'1')
print("Relay turned ON, Light turned ON")

# Close the serial port
ser.close()
