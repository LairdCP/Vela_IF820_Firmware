import common.ez_serial_port as ez_port

PORT_NAME = '/dev/cu.usbmodem334304'

ez = ez_port.open(PORT_NAME, 115200)

res = ez.sendAndWait('system_ping')

print(f'Ping result: {res}')
