#!/usr/bin/env python3

import argparse
import logging
import time
import common.EzSerialPort as ez_port
import common.SerialPort as serial_port
import common.PicoProbe as pico_probe
from common.BT900SerialPort import BT900SerialPort
from common.AppLogging import AppLogging
from common.CommonLib import CommonLib
from ezserial_host_api.ezslib import Packet

"""
Hardware Setup
This sample requires the following hardware:
-BT900 connected to PC via USB to act as a Bluetooth Central
-IF820 connected to PC via USB to act as a Bluetooth Peripheral
-PicoProbe connected to PC via USB.  GPIO16 of PicoProbe attached to P13 to IF820 Peripheral Device.
"""

INQUIRY_DURATION_SEC = 15
FLAG_INQUIRY_NAME = 1
SPP_DATA = "abcdefghijklmnop"
OK = "OK"


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
        app_logger = AppLogging("bt900-if820")
        app_logger.configure_app_logging(
            level=app_logger.DEBUG, file_level=app_logger.NOTSET)
        app_logger.app_log_info("Debugging mode enabled")

    common_lib = CommonLib()

    # open devices
    # bt900
    bt900_central = BT900SerialPort()
    open_result = bt900_central.device.open(
        args.connection_c, bt900_central.BT900_DEFAULT_BAUD)
    if (not open_result):
        raise Exception(
            f"Error!  Unable to open bt900 central at {args.connection_p}")

    # IF820
    if820_peripheral = ez_port.EzSerialPort()
    open_result = if820_peripheral.open(args.connection_p, 115200)
    if (not open_result):
        raise Exception(
            f"Error!  Unable to open ez_peripheral at {args.connection_p}")

    if820_peripheral.set_queue_timeout(5)

    # Pico Probe attached to peripheral
    pp_peripheral = pico_probe.PicoProbe()
    pp_peripheral.open(args.picoprobe_c)
    if (not pp_peripheral.is_open):
        app_logger.app_log_critical("Unable to open Pico Probe.")

    # ensure SPP enable on module by setting pico gpio to input
    # PicoProbe GPIO16 -> IF820 P13
    pp_peripheral.gpio_to_input(pp_peripheral.GPIO_16)

    # bt900 query firmware version
    response = bt900_central.get_bt900_fw_ver()
    app_logger.app_log_info(f"BT900 firmware version = {response}")

    # IF820 Ping
    ez_rsp = if820_peripheral.send_and_wait(if820_peripheral.CMD_PING)
    app_logger.app_log_debug(type(ez_rsp))
    common_lib.check_if820_response(if820_peripheral.CMD_PING, ez_rsp)

    # IF820 Factory Reset
    if820_peripheral.send(if820_peripheral.CMD_FACTORY_RESET,
                          apiformat=Packet.EZS_API_FORMAT_TEXT)
    ez_rsp = if820_peripheral.wait_event(if820_peripheral.EVENT_SYSTEM_BOOT)
    common_lib.check_if820_response(if820_peripheral.CMD_FACTORY_RESET, ez_rsp)

    time.sleep(0.5)
    if820_peripheral.clear_rx_queue()

    # if820 get mac address of peripheral
    response = if820_peripheral.send_and_wait(
        command=if820_peripheral.CMD_GET_BT_ADDR, apiformat=Packet.EZS_API_FORMAT_TEXT)
    common_lib.check_if820_response(if820_peripheral.CMD_GET_BT_ADDR, ez_rsp)
    str_mac = common_lib.if820_mac_addr_response_to_mac_as_string(
        response[1].payload.address)
    app_logger.app_log_info(str_mac)

    # bt900 enter command mode
    response = bt900_central.send_and_wait_for_response(
        bt900_central.BT900_CMD_MODE)
    common_lib.check_bt900_response(response[0])

    # bt900 delete all previous bonds
    response = bt900_central.send_and_wait_for_response(
        bt900_central.BT900_CMD_BTC_BOND_DEL)
    common_lib.check_bt900_response(response[0])

    # bt900 set io cap
    response = bt900_central.send_and_wait_for_response(
        bt900_central.BT900_CMD_BTC_IOCAP)
    common_lib.check_bt900_response(response[0])

    # bt900 set pairable
    response = bt900_central.send_and_wait_for_response(
        bt900_central.BT900_CMD_SET_BTC_PAIRABLE)
    common_lib.check_bt900_response(response[0])

    # bt900 spp connect
    connect_command = bt900_central.BT900_SPP_CONNECT_REQ + str_mac + bt900_central.CR
    response = bt900_central.send_and_wait_for_response(connect_command, 5)
    common_lib.check_bt900_response(response[0])

    # IF820 Event (Text Info contains "P")
    app_logger.app_log_info("Wait for IF820 Pairing Requested Event.")
    response = if820_peripheral.wait_event(
        event=if820_peripheral.EVENT_SMP_PAIRING_REQUESTED, rxtimeout=3)
    common_lib.check_if820_response(
        if820_peripheral.EVENT_SMP_PAIRING_REQUESTED, response)

    # bt900 event (Text Info contains "Pair Req")
    app_logger.app_log_info("Wait for BT900 Pair Request Event.")
    bt900_event = bt900_central.wait_for_response(
        rx_timeout_sec=bt900_central.DEFAULT_WAIT_TIME_SEC)
    common_lib.check_bt900_response(bt900_event, bt900_central.BT900_PAIR_REQ)

    # bt900 pair response
    response = bt900_central.send_and_wait_for_response(
        bt900_central.BT900_CMD_BTC_PAIR_RESPONSE)
    common_lib.check_bt900_response(response[0])

    # IF820 Event (Text Info contains "PR")
    app_logger.app_log_info("Wait for IF820 SMP Pairing Result Event.")
    response = if820_peripheral.wait_event(
        event=if820_peripheral.EVENT_SMP_PAIRING_RESULT)
    common_lib.check_if820_response(
        if820_peripheral.EVENT_SMP_PAIRING_RESULT, response)

    # bt900 event (Text Info contains "Pair Result")
    app_logger.app_log_info("Wait for BT900 SMP Pair Result.")
    bt900_event = bt900_central.wait_for_response(
        rx_timeout_sec=bt900_central.DEFAULT_WAIT_TIME_SEC)
    common_lib.check_bt900_response(
        bt900_event, bt900_central.BT900_PAIR_RESULT)

    # IF820 Event (Text Info contains "ENC")
    app_logger.app_log_info("Wait for IF820 SMP Encryption Status Event.")
    response = if820_peripheral.wait_event(
        event=if820_peripheral.EVENT_SMP_ENCRYPTION_STATUS)
    common_lib.check_if820_response(
        if820_peripheral.EVENT_SMP_PASSKEY_DISPLAY_REQUESTED, response)

    # IF820 Event
    app_logger.app_log_info("Wait for IF820 Bluetooth Connected Event.")
    response = if820_peripheral.wait_event(
        event=if820_peripheral.EVENT_BT_CONNECTED)
    common_lib.check_if820_response(
        if820_peripheral.EVENT_BT_CONNECTED, response)

    # bt900 event
    app_logger.app_log_info("Wait for BT900 SPP Connect Event.")
    bt900_event = bt900_central.wait_for_response(
        rx_timeout_sec=bt900_central.DEFAULT_WAIT_TIME_SEC)
    common_lib.check_bt900_response(
        bt900_event, bt900_central.BT900_SPP_CONNECT)

    time.sleep(1)

    # The two devices are connected.  We can now send data on SPP.
    # For the IF820 we need to close the ez_serial port instance and
    # then open a base serial port so we can send raw data with no processing.
    if820_peripheral.close()
    sp_peripheral = serial_port.SerialPort()
    result = sp_peripheral.open(args.connection_p, 115200)

    # send data from IF820 -> BT900
    for c in SPP_DATA:
        sp_peripheral.send(c)
        time.sleep(0.02)
    rx_data = bt900_central.device.get_rx_queue()
    string_utf8 = bytes(rx_data).decode('utf-8')
    app_logger.app_log_info(f"IF820->BT900 Data = {string_utf8}")

    # send data from BT900 -> IF820
    bt900_central.device.send(
        bt900_central.BT900_SPP_WRITE_PREFIX + SPP_DATA + bt900_central.CR)
    time.sleep(0.5)
    rx_data = sp_peripheral.get_rx_queue()
    string_utf8 = bytes(rx_data).decode('utf-8')
    app_logger.app_log_info(f"BT900->IF820 Data = {string_utf8}")

    # End SPP Mode on both devices, and close open connections.
    pp_peripheral.gpio_to_output(pp_peripheral.GPIO_16)
    pp_peripheral.gpio_to_output_high(pp_peripheral.GPIO_16)
    pp_peripheral.gpio_to_input(pp_peripheral.GPIO_16)
    pp_peripheral.close()
    bt900_central.device.send(bt900_central.BT900_SPP_DISCONNECT)
    time.sleep(0.5)
    bt900_central.device.send(bt900_central.BT900_EXIT)
    time.sleep(0.5)
    bt900_central.device.close()
    if820_peripheral.close()
