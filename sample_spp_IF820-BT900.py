import argparse
import logging
import time
import common.EzSerialPort as ez_port
import common.SerialPort as serial_port
import common.PicoProbe as pico_probe
from common.BT900SerialPort import BT900SerialPort
from common.CommonLib import CommonLib
from common.AppLogging import AppLogging
from ezserial_host_api.ezslib import Packet

SPP_DATA = "abcdefghijklmnop"

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-cp', '--connection_p',
                        required=True, help="Peripheral COM port")
    parser.add_argument('-cc', '--connection_c',
                        required=True, help="Central COM port")
    parser.add_argument('-ppc', '--picoprobe_c',
                        required=True, help="Pico Probe Id Central")
    parser.add_argument('-d', '--debug', action='store_true',
                        help="Enable verbose debug messages")
    logging.basicConfig(format='%(asctime)s: %(message)s', level=logging.INFO)
    args, unknown = parser.parse_known_args()
    if args.debug:
        app_logger = AppLogging("if820-bt900")
        app_logger.configure_app_logging(level=app_logger.DEBUG, file_level=app_logger.NOTSET)
        app_logger.app_log_info("Debugging mode enabled")

    common_lib = CommonLib()

    #open devices
    #bt900
    bt900_peripheral = BT900SerialPort()
    open_result = bt900_peripheral.device.open(args.connection_p, bt900_peripheral.BT900_DEFAULT_BAUD)
    if (not open_result):
        raise Exception(f"Error!  Unable to open bt900 peripheral at {args.connection_p}")

    #IF820
    if820_central = ez_port.EzSerialPort()
    open_result = if820_central.open(args.connection_c, 115200)
    if (not open_result):
        raise Exception(f"Error!  Unable to open ez_peripheral at {args.connection_c}")
    if820_central.set_queue_timeout(2)

    #Pico Probe attached to central
    pp_central = pico_probe.PicoProbe()
    pp_central.open(args.picoprobe_c)
    if (not pp_central.is_open):
         app_logger.app_log_critical("Unable to open Pico Probe.")

    #ensure SPP enable on module by setting pico gpio to input
    #PicoProbe GPIO16 -> IF820 P13
    pp_central.gpio_to_input(pp_central.GPIO_16)

    #bt900 query firmware version
    response = bt900_peripheral.get_bt900_fw_ver()
    app_logger.app_log_info(f"BT900 firmware version = {response}")

    #IF820 Ping
    ez_rsp = if820_central.send_and_wait(if820_central.CMD_PING)
    common_lib.check_if820_response(if820_central.CMD_PING, ez_rsp)

    #IF820 Factory Reset
    if820_central.send(if820_central.CMD_FACTORY_RESET)
    ez_rsp = if820_central.wait_event(if820_central.EVENT_SYSTEM_BOOT)
    common_lib.check_if820_response(if820_central.CMD_PING, ez_rsp)

    #bt900 get mac address of peripheral
    bt900_mac = bt900_peripheral.get_bt900_bluetooth_mac()
    app_logger.app_log_info(f"BT900 bluetooth mac addr = {bt900_mac}")

    #bt900 enter command mode
    response = bt900_peripheral.send_and_wait_for_response(bt900_peripheral.BT900_CMD_MODE)
    common_lib.check_bt900_response(response[0])

    #bt900 delete all previous bonds
    response = bt900_peripheral.send_and_wait_for_response(bt900_peripheral.BT900_CMD_BTC_BOND_DEL)
    common_lib.check_bt900_response(response[0])

    #bt900 set io cap
    response = bt900_peripheral.send_and_wait_for_response(bt900_peripheral.BT900_CMD_BTC_IOCAP)
    common_lib.check_bt900_response(response[0])

    #bt900 set pairable
    response = bt900_peripheral.send_and_wait_for_response(bt900_peripheral.BT900_CMD_SET_BTC_PAIRABLE)
    common_lib.check_bt900_response(response[0])

    #bt900 set connectable
    response = bt900_peripheral.send_and_wait_for_response(bt900_peripheral.BT900_CMD_SET_BTC_CONNECTABLE)
    common_lib.check_bt900_response(response[0])

    #bt900 set discoverable
    response = bt900_peripheral.send_and_wait_for_response(bt900_peripheral.BT900_CMD_SET_BTC_DISCOVERABLE)
    common_lib.check_bt900_response(response[0])

    #bt900 open spp port
    response = bt900_peripheral.send_and_wait_for_response(bt900_peripheral.BT900_CMD_SPP_OPEN)
    common_lib.check_bt900_response(response[0])

    #IF820(central) connect to BT900 (peripheral)
    conn_handle = None
    bt900_mac[1].reverse()
    response = if820_central.send_and_wait(command=if820_central.CMD_CONNECT,
                                         address=bt900_mac[1],
                                         apiformat=Packet.EZS_API_FORMAT_TEXT,
                                         type=1)
    common_lib.check_if820_response(if820_central.EVENT_SMP_PASSKEY_DISPLAY_REQUESTED, response)
    conn_handle = response[1]

    #IF820 Event (Text Info contains "P")
    app_logger.app_log_info("Wait for IF820 Pairing Requested Event.")
    response = if820_central.wait_event(event=if820_central.EVENT_SMP_PAIRING_REQUESTED)
    common_lib.check_if820_response(if820_central.EVENT_SMP_PAIRING_REQUESTED, response)

    #bt900 event (Text Info contains "Pair Req")
    app_logger.app_log_info("Wait for BT900 Pair Request Event.")
    bt900_event = bt900_peripheral.wait_for_response(rx_timeout_sec=bt900_peripheral.DEFAULT_WAIT_TIME_SEC)
    common_lib.check_bt900_response(bt900_event, bt900_peripheral.BT900_PAIR_REQ)

    #bt900 set pairable (Response is "OK")
    app_logger.app_log_info("Send BT900 Pair Request")
    response = bt900_peripheral.send_and_wait_for_response(bt900_peripheral.BT900_CMD_BTC_PAIR_RESPONSE)
    common_lib.check_bt900_response(response[0])

    #IF820 Event (Text Info contains "PR")
    app_logger.app_log_info("Wait for IF820 SMP Pairing Result Event.")
    response = if820_central.wait_event(event=if820_central.EVENT_SMP_PAIRING_RESULT)
    common_lib.check_if820_response(if820_central.EVENT_SMP_PAIRING_RESULT, response)

    #bt900 event (Text Info contains "Pair Result")
    app_logger.app_log_info("Wait for BT900 SMP Pair Result.")
    bt900_event = bt900_peripheral.wait_for_response(rx_timeout_sec=bt900_peripheral.DEFAULT_WAIT_TIME_SEC)
    common_lib.check_bt900_response(bt900_event, bt900_peripheral.BT900_PAIR_RESULT)

    #IF820 Event (Text Info contains "ENC")
    app_logger.app_log_info("Wait for IF820 SMP Encryption Status Event.")
    response = if820_central.wait_event(event=if820_central.EVENT_SMP_ENCRYPTION_STATUS)
    common_lib.check_if820_response(if820_central.EVENT_SMP_PASSKEY_DISPLAY_REQUESTED, response)

    #IF820 Event
    app_logger.app_log_info("Wait for IF820 Bluetooth Connected Event.")
    response = if820_central.wait_event(event=if820_central.EVENT_BT_CONNECTED)
    common_lib.check_if820_response(if820_central.EVENT_BT_CONNECTED, response)

    #bt900 event
    app_logger.app_log_info("Wait for BT900 SPP Connect Event.")
    bt900_event = bt900_peripheral.wait_for_response(rx_timeout_sec=bt900_peripheral.DEFAULT_WAIT_TIME_SEC)
    common_lib.check_bt900_response(bt900_event, bt900_peripheral.BT900_SPP_CONNECT)

    #The two devices are connected.  We can now send data on SPP.
    #For the IF820 we need to close the ez_serial port instance and
    #then open a base serial port so we can send raw data with no processing.
    if820_central.close()
    sp_central = serial_port.SerialPort()
    sp_central.open(args.connection_c, 115200)

    #send data from IF820 -> BT900
    for c in SPP_DATA:
        sp_central.send(c)
        time.sleep(0.02)
    rx_data = bt900_peripheral.device.get_rx_queue()
    string_utf8 = bytes(rx_data).decode('utf-8')
    app_logger.app_log_info(f"IF820->BT900 Data = {string_utf8}")

    #send data from BT900 -> IF820
    bt900_peripheral.device.send(bt900_peripheral.BT900_SPP_WRITE_PREFIX + SPP_DATA + bt900_peripheral.CR)
    time.sleep(0.5)
    rx_data = sp_central.get_rx_queue()
    string_utf8 = bytes(rx_data).decode('utf-8')
    app_logger.app_log_info(f"BT900->IF820 Data = {string_utf8}")

    #End SPP Mode on both devices, and close open connections.
    pp_central.gpio_to_output(pp_central.GPIO_16)
    pp_central.gpio_to_output_high(pp_central.GPIO_16)
    pp_central.gpio_to_input(pp_central.GPIO_16)
    pp_central.close()
    bt900_peripheral.device.send(bt900_peripheral.BT900_SPP_DISCONNECT)
    time.sleep(0.5)
    bt900_peripheral.device.send(bt900_peripheral.BT900_EXIT)
    time.sleep(0.5)
    bt900_peripheral.device.close()
    if820_central.close()



