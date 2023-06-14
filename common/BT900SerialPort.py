from common.SerialPort import SerialPort
import threading
import time
from common.AppLogging import AppLogging
from enum import Enum


class BT900SerialPort(AppLogging):

    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'

    CR = "\r"
    BT900_CMD_QUERY_FW = "ati 3" + CR
    BT900_CMD_QUERY_MAC_ADDR = "ati 4" + CR
    BT900_CMD_MODE = "cmd" + CR
    BT900_CMD_BTC_BOND_DEL = "btc bond delall" + CR
    BT900_CMD_BTC_IOCAP = "btc iocap 0" + CR
    BT900_CMD_BTC_JUST_WORKS = "btc justworks 0" + CR
    BT900_CMD_SET_BTC_PAIRABLE = "btc setpairable 1" + CR
    BT900_CMD_SET_BTC_CONNECTABLE = "btc setconnectable 1" + CR
    BT900_CMD_SET_BTC_DISCOVERABLE = "btc setdiscoverable 1 30" + CR
    BT900_CMD_INQUIRY_CONFIG = "inquiry config 1 2" + CR
    BT900_CMD_INQUIRY_START = "inquiry start 5" + CR
    BT900_CMD_SPP_CONNECT = "spp connect" + CR
    BT900_CMD_SPP_OPEN = "spp open" + CR
    BT900_CMD_BTC_PAIR_RESPONSE = "btc pairresp 1" + CR
    BT900_SPP_WRITE_PREFIX = "spp write 1 "
    BT900_SPP_DISCONNECT = "spp disconnect 1" + CR
    BT900_DISCONNECT = "disconnect 1" + CR
    BT900_EXIT = "exit" + CR
    BT900_PAIR_REQ = "Pair Req:"
    BT900_PAIR_RESULT = "Pair Result:"
    BT900_SPP_CONNECT = "SPP Connect:"
    BT900_SPP_CONNECT_REQ = "spp connect "
    BT900_CYSPP_CONNECT = "connect "
    BT900_GATTC_OPEN = "gattc open 512 0"
    BT900_ENABLE_CYSPP_NOT = "gattc write 1 18 0100"
    BT900_CYSPP_WRITE_DATA_STRING = "gattc writecmd$ 1 17 "

    BT900_Periperhal = None
    BT900_Central = None

    BT900_DEFAULT_BAUD = 115200
    DEFAULT_WAIT_TIME_SEC = 1
    ERROR_DEVICE_TYPE = "Error!  Unknown Device Type."

    class DeviceType(Enum):
        PERIPHERAL = 1
        CENTRAL = 2

    def __init__(self):
        super().__init__('bt900_serial_port')
        self.device = SerialPort()
        self.configure_app_logging(self.NOTSET, self.NOTSET)

    def get_device(self):
        return self.device

    def send_and_wait_for_response(self, msg: str, rx_timeout_sec: int = DEFAULT_WAIT_TIME_SEC):
        rx_data = []
        self.device.clear_rx_queue()
        self.device.send(msg)
        rx_data = self.wait_for_response(rx_timeout_sec)
        str_response = self.response_to_string(rx_data)
        return rx_data, str_response

    def check_for_end_of_packet(self, rx_timeout_event, rx_data):
        if (len(rx_data) > 2):
            if (rx_data[-1] == 0x0d):
                # we have received the packet, return it right away
                # self.app_logger.app_log_debug("BT900 End Of Packet Detected.")
                rx_timeout_event.set()

    def rx_timeout_worker(self, rx_timeout_event, rx_timeout_sec: float):
        # self.app_logger.app_log_debug("BT900 rx_timeout_worker starting wait")
        rx_timeout_event.wait(rx_timeout_sec)
        # self.app_logger.app_log_debug("BT900 rx_timeout_worker timeout.")
        rx_timeout_event.set()

    def wait_for_response(self, rx_timeout_sec: float):
        rx_data = []
        rx_timeout_event = threading.Event()
        thread = threading.Thread(target=self.rx_timeout_worker, args=(
            rx_timeout_event, rx_timeout_sec))
        thread.start()
        while (not rx_timeout_event.is_set()):
            rx_data = self.device.get_rx_queue()
            self.check_for_end_of_packet(rx_timeout_event, rx_data)
            time.sleep(0.02)
        return rx_data

    def parse_response(self, response: str):
        rsp_parts = []
        rsp_parts = response.split("\t")
        if (len(rsp_parts) > 2):
            value_part = rsp_parts[2].split("\r")
            parse_rsp = {"direction": rsp_parts[0].removeprefix("\n"),
                         "msgId": rsp_parts[1].removeprefix("\n"),
                         "val": value_part[0]}
        return parse_rsp

    def response_to_string(self, response):
        str_result = bytes(response).decode('utf-8')
        return str_result

    def get_bt900_fw_ver(self):
        response = self.send_and_wait_for_response(msg=self.BT900_CMD_QUERY_FW)
        response_parts = self.parse_response(response[1])
        fw_ver = response_parts["val"]
        return fw_ver

    def get_bt900_bluetooth_mac(self):
        response = self.send_and_wait_for_response(
            msg=self.BT900_CMD_QUERY_MAC_ADDR)
        response_parts = self.parse_response(response[1])
        mac = response_parts["val"]
        mac_parts = mac.split(' ')
        str_mac = mac_parts[1]
        # covert to list-of-bytes
        mac_bytes = bytes.fromhex(str_mac)
        list_bytes_mac = list(mac_bytes)
        return str_mac, list_bytes_mac
