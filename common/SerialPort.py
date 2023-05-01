import time
import serial
import threading
import queue
import sys
from common.AppLogging import AppLogging

sys.path.append("..")  # Adds parent directory to python modules path

CLEAR_QUEUE_TIMEOUT_DEFAULT = 5
SUCCESS = 0
ERROR_NO_RESPONSE   = -1
ERROR_RESPONSE   = -2

class SerialPort(AppLogging):
    """Base serial port implementation
    """
    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'

    def __init__(self):
        super().__init__('serial_port')
        self.port = None
        self.ez = None
        self.rx_queue = None
        self.stop_threads = False
        self.clear_queue_timeout_sec = CLEAR_QUEUE_TIMEOUT_DEFAULT
        self.queue_monitor_event = threading.Event()
        self.configure_app_logging(self.NOTSET, self.NOTSET)


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
                    AppLogging.app_log_debug(f'Clear RX queue ({curr_len})')
                    self.clear_rx_queue()
                    # TODO: Instead of clearing the queue, see if a packet can be parsed and fire an event
                else:
                    AppLogging.app_log_debug(f'RX queue len: {curr_len}')
                last_len = curr_len
            time.sleep(self.clear_queue_timeout_sec)

    def __serial_port_rx_thread(self):
        while True:
            if self.stop_threads:
                break
            try:
                bytes = self.port.read(1)
                for byte in bytes:
                    self.rx_queue.put(byte)
                    AppLogging.app_log_debug(f'RX: {hex(byte)}')
            except:
                pass

    def set_queue_timeout(self, timeout_sec):
        self.clear_queue_timeout_sec = timeout_sec

    def open(self, portName: str, baud: int) -> bool:
        """Open the serial port

        Args:
            portName (str): COM port name or device
            baud (int): baud rate

        Returns:
            bool: true on success
        """
        success = False
        self.port = serial.Serial(portName, baud, rtscts=True)
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
        success = True
        return success

    def clear_rx_queue(self):
        """Clear all received bytes from the queue
        """
        with self.rx_queue.mutex:
            self.rx_queue.queue.clear()

    def send(self, text: str):
        """Send command

        Args:
            command (str): data to send

        Returns:
            none
            """
        self.app_log_info(bytearray(text, "utf-8"))
        self.port.write(bytearray(text, "utf-8"))

    def close(self):
        self.stop_threads = True
        if self.port and self.port.is_open:
            self.port.close()
            self.app_log_info("close")

    def get_rx_queue(self):
        return self.rx_queue.queue

    def is_queue_empty(self):
        return self.rx_queue.empty()
