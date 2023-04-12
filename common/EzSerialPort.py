import ezserial_host_api.ezslib as ez_serial
import time
import serial
import threading
import queue
import sys
from AppLogging import AppLogging
sys.path.append("..")  # Adds parent directory to python modules path

CLEAR_QUEUE_TIMEOUT = 0.1
SUCCESS = 0
ERROR_NO_RESPONSE = -1
ERROR_RESPONSE = -2

class EzSerialPort(AppLogging):
    """Serial port implementation to communicate with EZ-Serial devices
    """
    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'

    def __init__(self):
        self.port = None
        self.ez = None
        self.rx_queue = None
        self.stop_threads = False
        self.queue_monitor_event = threading.Event()
        self.app_logger = AppLogging()
        self.app_logger.configure_app_logging(root_level=self.app_logger.NOTSET,
                                         stdout_level=self.NOTSET,
                                         file_level=self.NOTSET,
                                         log_file_name="EzSerialPort.log")
    def __queue_monitor(self):
        last_len = 0
        curr_len = 0
        while True:
            if self.stop_threads:
                break
            self.queue_monitor_event.wait()
            if not self.rx_queue.empty():
                curr_len = self.rx_queue.qsize()
                if curr_len == last_len:
                    self.app_logger.app_log_debug(f'Clear RX queue ({curr_len})')
                    self.clear_rx_queue()
                    # TODO: Instead of clearing the queue, see if a packet can be parsed and fire an event
                else:
                    self.app_logger.app_log_debug(f'RX queue len: {curr_len}')
                last_len = curr_len
            time.sleep(CLEAR_QUEUE_TIMEOUT)

    def __pause_queue_monitor(self):
        self.queue_monitor_event.clear()

    def __resume_queue_monitor(self):
        self.queue_monitor_event.set()

    def __serial_port_rx_thread(self):
        while True:
            if self.stop_threads:
                break
            try:
                bytes = self.port.read(1)
                for byte in bytes:
                    self.rx_queue.put(byte)
                    self.app_logger.app_log_debug(f'RX: {hex(byte)}')
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

        # if the port is already open just return
        if self.port and self.port.is_open:
            return

        self.ez = ez_serial.API(hardwareOutput=self.__write_bytes,
                                hardwareInput=self.__read_bytes)
        self.port = serial.Serial(portName, baud)
        self.port.timeout = None
        self.port.reset_input_buffer()
        self.port.reset_output_buffer()
        self.rx_queue = queue.Queue()
        self.stop_threads = False
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

    def send_and_wait(self, command: str, apiformat: int = None, rxtimeout: int = False, **kwargs) -> tuple:
        """Send command and wait for a response

        Args:
            command (str): Command to send
            apiformat (int, optional): API format to use 0=text, 1=binary. Defaults to None.
            rxtimeout (int, optional): Time to wait for response (in seconds). Defaults to False (Receive immediately).

        Returns:
            int: 0 for success, else error. This is the received packet result code.
        """
        self.__pause_queue_monitor()
        res = self.ez.sendAndWait(
            command=command, apiformat=apiformat, rxtimeout=rxtimeout, **kwargs)
        if res[0] == None:
            self.__resume_queue_monitor()
            return (ERROR_NO_RESPONSE, None)
        else:
            error = res[0].payload.get('error', None)
            if error:
                self.__resume_queue_monitor()
                return (ERROR_RESPONSE, None)
            else:
                self.__resume_queue_monitor()
                return (SUCCESS, res[0])

    def send(self, command: str, apiformat: int = None, rxtimeout: int = False, **kwargs):
        """Send command

        Args:
            command (str): Command to send
            apiformat (int, optional): API format to use 0=text, 1=binary. Defaults to None.

        Returns:
            none
            """
        self.ez.sendCommand(command=command, apiformat=apiformat, **kwargs)

    def wait_event(self, event: str, rxtimeout: int = False) -> tuple:
        """Wait for an event to be received

        Args:
            event (str): The event to wait for
            rxtimeout (int, optional): Time to wait for the event. Defaults to False (Don't wait).

        Returns:
            tuple: (err code - 0 for success else error, Packet object)
        """
        self.__pause_queue_monitor()
        res = self.ez.waitEvent(event, rxtimeout)
        if res[0] == None:
            self.__resume_queue_monitor()
            return (-1, None)
        else:
            self.__resume_queue_monitor()
            return (0, res[0])

    def close(self):
        self.stop_threads = True
        if self.port and self.port.is_open:
            self.port.close()

    def set_api_format(self, api: int):
        """Set API format to use for sending commands

        Args:
            api (int): 0 = TEXT, 1 = BINARY
        """
        self.ez.defaults.apiformat = api