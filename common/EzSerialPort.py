import ezserial_host_api.ezslib as ez_serial
import logging
import time
import serial
import threading
import queue
import sys
sys.path.append("..")  # Adds parent directory to python modules path

CLEAR_QUEUE_TIMEOUT = 0.1


class EzSerialPort:
    """Serial port implementation to communicate with EZ-Serial devices
    """

    def __init__(self):
        self.port = None
        self.ez = None
        self.rx_queue = None

    def __queue_monitor(self):
        last_len = 0
        curr_len = 0
        while True:
            time.sleep(CLEAR_QUEUE_TIMEOUT)
            if not self.rx_queue.empty():
                curr_len = self.rx_queue.qsize()
                if curr_len == last_len:
                    logging.debug(f'Clear RX queue ({curr_len})')
                    self.clear_rx_queue()
                    # TODO: Instead of clearing the queue, see if a packet can be parsed and fire an event
                else:
                    logging.debug(f'RX queue len: {curr_len}')
                last_len = curr_len

    def __serial_port_rx_thread(self):
        while True:
            try:
                bytes = self.port.read(1)
                for byte in bytes:
                    self.rx_queue.put(byte)
            except:
                pass

    def __write_bytes(self, bytes):
        res = self.port.write(bytes)
        return (bytes, res)

    def __read_bytes(self, rxtimeout):
        res = self.ez.EZS_INPUT_RESULT_NO_DATA
        byte = None
        block = True
        if rxtimeout == None or rxtimeout == 0:
            block = False
        try:
            byte = self.rx_queue.get(block, rxtimeout)
            res = self. ez.EZS_INPUT_RESULT_BYTE_READ
        except queue.Empty:
            pass
        return (byte, res)

    def open(self, portName: str, baud: int) -> tuple:
        """Open the serial port and init the EZ-Serial API

        Args:
            portName (str): COM port name or device
            baud (int): baud rate

        Returns:
            tuple: (EZ-Serial API object, Serial Port Object)
        """

        self.ez = ez_serial.API(hardwareOutput=self.__write_bytes,
                                hardwareInput=self.__read_bytes)
        self.port = serial.Serial(portName, baud)
        self.port.timeout = None
        self.port.reset_input_buffer()
        self.port.reset_output_buffer()
        self.rx_queue = queue.Queue()
        # The serial port RX thread reads all bytes received and places them in a queue
        threading.Thread(target=self.__serial_port_rx_thread,
                         daemon=True).start()
        # The queue monitor thread clears stray RX bytes if they are not processed for
        # CLEAR_QUEUE_TIMEOUT amount of time
        threading.Thread(target=self.__queue_monitor, daemon=True).start()
        return (self.ez, self.port)

    def clear_rx_queue(self):
        """Clear all received bytes from the queue
        """
        with self.rx_queue.mutex:
            self.rx_queue.queue.clear()

    def send_and_wait(self, command: str, apiformat: int = None, rxtimeout: int = False, **kwargs) -> int:
        """Send command and wait for a response

        Args:
            command (str): Command to send
            apiformat (int, optional): API format to use 0=text, 1=binary. Defaults to None.
            rxtimeout (int, optional): Time to wait for response (in seconds). Defaults to False.

        Returns:
            int: 0 for success, else error. This is the received packet result code.
        """
        res = self.ez.sendAndWait(
            command=command, apiformat=apiformat, rxtimeout=rxtimeout, **kwargs)
        if res[0] == None:
            return -1
        else:
            return res[0].payload['result']
