import serial

ser = serial.Serial('COM4')
ser.baudrate = 115200

while(1):
    message = '.'
    messate_bytes = message.encode()
    ser.write(messate_bytes)
    response =  ser.readline()
    decoded_bytes = response[0:len(response)-2].decode("utf-8")
    print(decoded_bytes)