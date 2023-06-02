import ezserial_host_api.ezslib as ez_serial
import time
import serial
import threading
import queue
import sys
from common.AppLogging import AppLogging
from enum import Enum
sys.path.append("..")  # Adds parent directory to python modules path

CLEAR_QUEUE_TIMEOUT_DEFAULT = 0.1
SUCCESS = 0
ERROR_NO_RESPONSE = -1
ERROR_RESPONSE = -2


class SystemCommands:
    @property
    def CMD_PING(self): return "system_ping"
    @property
    def CMD_REBOOT(self): return "system_reboot"
    @property
    def CMD_DUMP(self): return "system_dump"
    @property
    def CMD_STORE_CONFIG(self): return "system_store_config"
    @property
    def CMD_FACTORY_RESET(self): return "system_factory_reset"
    @property
    def CMD_QUERY_FW(self): return "system_query_firmware_version"
    @property
    def CMD_QUERY_UID(self): return "system_query_unique_id"
    @property
    def CMD_QUERY_RANDOM_NUM(self): return "system_query_random_number"
    @property
    def CMD_AES_ENCRYPT(self): return "system_aes_encrypt"
    @property
    def CMD_AES_DECRYPT(self): return "system_aes_decrypt"
    @property
    def CMD_WRITE_USER_DATA(self): return "system_write_user_data"
    @property
    def CMD_READ_USER_DATA(self): return "system_read_user_data"
    @property
    def CMD_SET_BT_ADDR(self): return "system_set_bluetooth_address"
    @property
    def CMD_GET_BT_ADDR(self): return "system_get_bluetooth_address"
    @property
    def CMD_SET_ECO_PARAMS(self): return "system_set_eco_parameters"
    @property
    def CMD_GET_ECO_PARAMS(self): return "system_get_eco_parameters"
    @property
    def CMD_SET_WCO_PARAMS(self): return "system_set_wco_parameters"
    @property
    def CMD_GET_WCO_PARAMS(self): return "system_get_wco_parameters"
    @property
    def CMD_SET_SLEEP_PARAMS(self): return "system_set_sleep_parameters"
    @property
    def CMD_GET_SLEEP_PARAMS(self): return "system_get_sleep_parameters"
    @property
    def CMD_SET_TX_POWER(self): return "system_set_tx_power"
    @property
    def CMD_GET_TX_POWER(self): return "system_get_tx_power"
    @property
    def CMD_SET_TRANSPORT(self): return "system_set_transport"
    @property
    def CMD_GET_TRANSPORT(self): return "system_get_transport"
    @property
    def CMD_SET_UART_PARAMS(self): return "system_set_uart_parameters"
    @property
    def CMD_GET_UART_PARAMS(self): return "system_get_uart_parameters"

    @property
    def EVENT_SYSTEM_BOOT(self): return "system_boot"
    @property
    def EVENT_SYSTEM_ERROR(self): return "system_error"

    @property
    def EVENT_SYSTEM_FACTORY_RESET_COMPLETE(
        self): return "system_factory_reset_complete"

    @property
    def EVENT_SYSTEM_BOOT_FACTORY_TEST_ENTERED(
        self): return "system_factory_test_entered"

    @property
    def EVENT_SYSTEM_BOOT_DUMP_BLOB(self): return "system_dump_blob"


class BluetoothCommands:
    @property
    def CMD_START_INQUIRY(self): return "bt_start_inquiry"
    @property
    def CMD_CANCEL_INQUIRY(self): return "bt_cancel_inquiry"
    @property
    def CMD_QUERY_NAME(self): return "bt_query_name"
    @property
    def CMD_CONNECT(self): return "bt_connect"
    @property
    def CMD_CANCEL_CONNECTION(self): return "bt_cancel_connection"
    @property
    def CMD_DISCONNECT(self): return "bt_disconnect"
    @property
    def CMD_QUERY_CONNECTIONS(self): return "bt_query_connections"
    @property
    def CMD_QUERY_PEER_ADDR(self): return "bt_query_peer_address"
    @property
    def CMD_QUERY_RSSI(self): return "bt_query_rssi"
    @property
    def CMD_SET_DEVICE_CLASS(self): return "bt_set_device_class"
    @property
    def CMD_GET_DEVICE_CLASS(self): return "bt_get_device_class"
    @property
    def EVENT_INQUIRY_RESULT(self): return "bt_inquiry_result"
    @property
    def EVENT_NAME_RESULT(self): return "bt_name_result"
    @property
    def EVENT_INQUIRY_COMPLETE(self): return "bt_inquiry_complete"
    @property
    def EVENT_BT_CONNECTED(self): return "bt_connected"
    @property
    def EVENT_BT_CONN_STATUS(self): return "bt_connection_status"
    @property
    def EVENT_CONN_FAILED(self): return "bt_connection_failed"
    @property
    def EVENT_BT_DISCONNECTED(self): return "bt_disconnected"


class SmpCommands:
    @property
    def EVENT_SMP_BOND_ENTRY(self): return "smp_bond_entry"
    @property
    def EVENT_SMP_PAIRING_REQUESTED(self): return "smp_pairing_requested"
    @property
    def EVENT_SMP_PAIRING_RESULT(self): return "smp_pairing_result"
    @property
    def EVENT_SMP_ENCRYPTION_STATUS(self): return "smp_encryption_status"

    @property
    def EVENT_SMP_PASSKEY_DISPLAY_REQUESTED(
        self): return "smp_passkey_display_requested"


class GapCommands:
    @property
    def CMD_GAP_STOP_ADV(self): return "gap_stop_adv"
    @property
    def CMD_GAP_SET_ADV_PARAMETERS(self): return "gap_set_adv_parameters"
    @property
    def CMD_GAP_SET_ADV_DATA(self): return "gap_set_adv_data"
    @property
    def CMD_GAP_START_ADV(self): return "gap_start_adv"
    @property
    def CMD_GAP_START_SCAN(self): return "gap_start_scan"
    @property
    def EVENT_GAP_SCAN_RESULT(self): return "gap_scan_result"
    @property
    def CMD_GAP_STOP_SCAN(self): return "gap_stop_scan"
    @property
    def CMD_GAP_CONNECT(self): return "gap_connect"
    @property
    def EVENT_GAP_CONNECTED(self): return "gap_connected"


class GattServerCommands:
    @property
    def CMD_GATTS_CREATE_ATTR(self): return "gatts_create_attr"
    @property
    def CMD_GATTS_WRITE_HANDLE(self): return "gatts_write_handle"
    @property
    def CMD_GATTS_NOTIFY_HANDLE(self): return "gatts_notify_handle"


class GattClientCommands:
    @property
    def CMD_GATTC_READ_HANDLE(self): return "gattc_read_handle"
    @property
    def CMD_GATTC_WRITE_HANDLE(self): return "gattc_write_handle"
    @property
    def EVENT_GATTC_DATA_RECEIVED(self): return "gattc_data_received"


class GapAdvertMode(Enum):
    NA = 0  # TODO: This does not match the user guide


class GapAdvertType(Enum):
    STOP = 0
    DIRECTED_HIGH_DUTY_CYCLE = 1
    DIRECTED_LOW_DUTY_CYCLE = 2
    UNDIRECTED_HIGH_DUTY_CYCLE = 3
    UNDIRECTED_LOW_DUTY_CYCLE = 4
    NON_CONNECTABLE_HIGH_DUTY_CYCLE = 5
    NON_CONNECTABLE_LOW_DUTY_CYCLE = 6
    DISCOVERABLE_HIGH_DUTY_CYCLE = 7
    DISCOVERABLE_LOW_DUTY_CYCLE = 8


class GapAdvertChannels(Enum):
    CHANNEL_37 = 0x01
    CHANNEL_38 = 0x02
    CHANNEL_39 = 0x04
    CHANNEL_ALL = 0x07


class GapAdvertFlags(Enum):
    AUTO_MODE = 0x01    # Enable automatic advertising mode upon boot/disconnection
    CUSTOM_DATA = 0x02  # Use custom advertisement and scan response data
    ALL = 0x03


class GapAddressType(Enum):
    PUBLIC = 0
    RANDOM = 1


class GapScanMode(Enum):
    NA = 1  # TODO: This does not match the user guide


class GapScanFilter(Enum):
    NA = 0


class GattAttrType(Enum):
    STRUCTURE = 0
    VALUE = 1


class GattAttrPermission(Enum):
    VAR_LEN = 0x01
    READ = 0x02
    WRITE_NO_ACK = 0x04
    WRITE_ACK = 0x08
    AUTH_READ = 0x10
    RELIABLE_WRITE = 0x20
    AUTH_WRITE = 0x40


class GattAttrCharProps(Enum):
    BROADCAST = 0x01
    READ = 0x02
    WRITE_NO_RESP = 0x04
    WRITE = 0x08
    NOTIFY = 0x10
    INDICATE = 0x20
    SIGNED_WRITE = 0x40
    EXTENDED_PROPS = 0x80


class EzSerialPort(AppLogging, SystemCommands, BluetoothCommands,
                   SmpCommands, GapCommands, GattServerCommands,
                   GattClientCommands):
    """Serial port implementation to communicate with EZ-Serial devices
    """
    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'

    IF820_DEFAULT_BAUD = 115200

    def __init__(self):
        super().__init__('ez_serial_port')
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
                    self.app_log_debug(
                        f'Clear RX queue ({curr_len})')
                    self.clear_rx_queue()
                    # TODO: Instead of clearing the queue, see if a packet can be parsed and fire an event
                else:
                    self.app_log_debug(f'RX queue len: {curr_len}')
                last_len = curr_len
            time.sleep(self.clear_queue_timeout_sec)

    def __pause_queue_monitor(self):
        self.queue_monitor_event.clear()

    def __resume_queue_monitor(self):
        self.queue_monitor_event.set()

    def __serial_port_rx_thread(self):
        while True:
            if self.stop_threads:
                break
            try:
                data = self.port.read(1)
                for byte in data:
                    self.rx_queue.put(byte)
                    self.app_log_debug(f'RX: {hex(byte)}')
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

    def set_queue_timeout(self, timeout_sec):
        self.clear_queue_timeout_sec = timeout_sec

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

    def send_and_wait(self, command: str, apiformat: int = None, rxtimeout: int = 1, clear_queue: bool = True, **kwargs) -> tuple:
        """Send command and wait for a response

        Args:
            command (str): Command to send
            apiformat (int, optional): API format to use 0=text, 1=binary. Defaults to None.
            rxtimeout (int, optional): Time to wait for response (in seconds). Defaults to False (Receive immediately).

        Returns:
            int: 0 for success, else error. This is the received packet result code.
        """
        self.__pause_queue_monitor()
        if clear_queue:
            self.clear_rx_queue()
        res = self.ez.sendAndWait(
            command=command, apiformat=apiformat, rxtimeout=rxtimeout, **kwargs)
        if res[0] == None:
            self.__resume_queue_monitor()
            return (ERROR_NO_RESPONSE, None)
        else:
            error = res[0].payload.get('error', None)
            result = res[0].payload.get('result', None)
            if error:
                self.__resume_queue_monitor()
                return (ERROR_RESPONSE, None)
            elif result:
                self.__resume_queue_monitor()
                return (result, res[0])
            else:
                self.__resume_queue_monitor()
                return (SUCCESS, res[0])

    def send(self, command: str, apiformat: int = None, rxtimeout: int = 1, **kwargs):
        """Send command

        Args:
            command (str): Command to send
            apiformat (int, optional): API format to use 0=text, 1=binary. Defaults to None.

        Returns:
            none
            """
        self.ez.sendCommand(command=command, apiformat=apiformat, **kwargs)

    def wait_event(self, event: str, rxtimeout: int = 1) -> tuple:
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

    # these functions are needed to give the robot framework access
    # to inherited classes
    def get_sys_commands(self):
        return SystemCommands()

    def get_bluetooth_commands(self):
        return BluetoothCommands()

    def get_smp_commands(self):
        return SmpCommands()
