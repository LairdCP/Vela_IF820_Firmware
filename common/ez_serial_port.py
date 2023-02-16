import ezserial_host_api.ezslib as ez_serial
import serial
import sys
sys.path.append("..") # Adds parent directory to python modules path

port = None
ez = None


def write_bytes(bytes):
    res = port.write(bytes)
    return (bytes, res)


def read_bytes(rxtimeout):
    res = ez.EZS_INPUT_RESULT_NO_DATA
    byte = None
    if rxtimeout == None:
        port.timeout = 0
    else:
        port.timeout = rxtimeout
    bytes = port.read(1)
    if (len(bytes) == 1):
        res = ez.EZS_INPUT_RESULT_BYTE_READ
        byte = bytes[0]
    return (byte, res)


def open(portName, baud):
    global port
    global ez
    ez = ez_serial.API(hardwareOutput=write_bytes, hardwareInput=read_bytes)
    port = serial.Serial(portName, baud)
    return ez
