import ezserial_host_api.ezslib as ez_serial
import logging
import time
import serial
import threading
import queue
import sys
sys.path.append("..")  # Adds parent directory to python modules path

CLEAR_QUEUE_TIMEOUT = 0.1


def _queue_monitor():
    global rx_queue
    last_len = 0
    curr_len = 0
    while True:
        time.sleep(CLEAR_QUEUE_TIMEOUT)
        if not rx_queue.empty():
            curr_len = rx_queue.qsize()
            if curr_len == last_len:
                logging.debug(f'Clear RX queue ({curr_len})')
                clear_rx_queue()
                # TODO: Instead of clearing the queue, see if a packet can be parsed and fire an event
            else:
                logging.debug(f'RX queue len: {curr_len}')
            last_len = curr_len


def _serial_port_rx_thread():
    while True:
        try:
            bytes = port.read(1)
            for byte in bytes:
                rx_queue.put(byte)
        except:
            pass


def _write_bytes(bytes):
    res = port.write(bytes)
    return (bytes, res)


def _read_bytes(rxtimeout):
    res = ez.EZS_INPUT_RESULT_NO_DATA
    byte = None
    block = True
    if rxtimeout == None or rxtimeout == 0:
        block = False
    try:
        byte = rx_queue.get(block, rxtimeout)
        res = ez.EZS_INPUT_RESULT_BYTE_READ
    except queue.Empty:
        pass
    return (byte, res)


def open(portName: str, baud: int):
    """Open the serial port and init the EZ-Serial API

    Args:
        portName (str): COM port name or device
        baud (int): baud rate

    Returns:
        tuple: (EZ-Serial API object, Serial Port Object)
    """

    global port
    global ez
    global rx_queue
    ez = ez_serial.API(hardwareOutput=_write_bytes, hardwareInput=_read_bytes)
    port = serial.Serial(portName, baud)
    port.timeout = None
    port.reset_input_buffer()
    port.reset_output_buffer()
    rx_queue = queue.Queue()
    # The serial port RX thread reads all bytes received and places them in a queue
    threading.Thread(target=_serial_port_rx_thread, daemon=True).start()
    # The queue monitor thread clears stray RX bytes if they are not processed for
    # CLEAR_QUEUE_TIMEOUT amount of time
    threading.Thread(target=_queue_monitor, daemon=True).start()
    return (ez, port)


def clear_rx_queue():
    """Clear all received bytes from the queue
    """
    with rx_queue.mutex:
        rx_queue.queue.clear()
