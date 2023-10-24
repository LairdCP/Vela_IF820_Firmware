#!/usr/bin/env python3

import argparse
import logging
import time
import sys
sys.path.append('./common_lib')
import common_lib.SerialPort as serial_port
from common_lib.BT900SerialPort import BT900SerialPort
from common_lib.CommonLib import CommonLib
from common_lib.ezserial_host_api.ezslib import Packet
from common_lib.If820Board import If820Board

"""
Hardware Setup
This sample requires the following hardware:
-BT900 connected to PC via USB to act as a Bluetooth Central
-IF820 connected to PC via USB to act as a Bluetooth Peripheral

*Note the BT900 has to be manually reset between runs
as there is no way to take it out of data mode.
"""

CYSPP_DATA = "abcdefghijklmnop"
OK = "OK"
BT900_MAC_PREFIX = "01"


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-cc', '--connection_c',
                        required=True, help="Central COM port")
    parser.add_argument('-d', '--debug', action='store_true',
                        help="Enable verbose debug messages")
    args, unknown = parser.parse_known_args()
    logging.basicConfig(format='%(asctime)s: %(message)s', level=logging.INFO)
    if args.debug:
        logging.info("Debugging mode enabled")
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.info("Debugging mode disabled")

    common_lib = CommonLib()

    # open devices
    # bt900
    bt900_central = BT900SerialPort()
    bt900_central.device.open(
        args.connection_c, bt900_central.BT900_DEFAULT_BAUD)

    # IF820
    if820_board_p = If820Board.get_board()
    if820_board_p.open_and_init_board()
    if820_board_p.p_uart.set_queue_timeout(5)

    # bt900 query firmware version
    response = bt900_central.get_bt900_fw_ver()
    logging.info(f"BT900 firmware version = {response}")

    # IF820 Ping
    ez_rsp = if820_board_p.p_uart.send_and_wait(if820_board_p.p_uart.CMD_PING)
    logging.info(type(ez_rsp))
    common_lib.check_if820_response(if820_board_p.p_uart.CMD_PING, ez_rsp)

    # if820 get mac address of peripheral
    response = if820_board_p.p_uart.send_and_wait(
        command=if820_board_p.p_uart.CMD_GET_BT_ADDR, apiformat=Packet.EZS_API_FORMAT_TEXT)
    common_lib.check_if820_response(
        if820_board_p.p_uart.CMD_GET_BT_ADDR, ez_rsp)
    # note the BT900 requires a 01 prefix to the start of the MAC address
    str_mac = BT900_MAC_PREFIX + common_lib.if820_mac_addr_response_to_mac_as_string(
        response[1].payload.address)
    logging.info(str_mac)

    # bt900 enter command mode
    response = bt900_central.send_and_wait_for_response(
        bt900_central.BT900_CMD_MODE)
    common_lib.check_bt900_response(response[0])

    # if820 advertise
    response = if820_board_p.p_uart.send_and_wait(
        command=if820_board_p.p_uart.CMD_GAP_START_ADV,
        apiformat=Packet.EZS_API_FORMAT_TEXT,
        mode=2,
        type=3,
        channels=7,
        high_interval=0x30,
        high_duration=0x1e,
        low_interval=0x800,
        low_duration=0x3c,
        flags=0,
        directAddr=0,
        directAddrType=0)

    # bt900 cyspp connect
    # note:  the bt900 central could scan for devices and pick out the appropriate device to connect to.
    # however for simplicity since we already know its address we will skip that step and just connect.
    connect_command = bt900_central.BT900_CYSPP_CONNECT + \
        str_mac + " 50 30 30 50" + bt900_central.CR
    response = bt900_central.send_and_wait_for_response(connect_command, 5)
    common_lib.check_bt900_response(response[0])

    # IF820 Event (Text Info contains "C" for connect)
    logging.info("Wait for IF820 Connected Event.")
    response = if820_board_p.p_uart.wait_event(
        event=if820_board_p.p_uart.EVENT_GAP_CONNECTED, rxtimeout=3)
    common_lib.check_if820_response(
        if820_board_p.p_uart.EVENT_GAP_CONNECTED, response)

    # IF820 Event (Text Info contains "CU" for connection updated)
    logging.info("Wait for IF820 Connection Updated Event.")
    response = if820_board_p.p_uart.wait_event(
        event=if820_board_p.p_uart.EVENT_GAP_CONNECTION_UPDATED, rxtimeout=3)
    common_lib.check_if820_response(
        if820_board_p.p_uart.EVENT_GAP_CONNECTION_UPDATED, response)

    # bt900 open gattc
    response = bt900_central.send_and_wait_for_response(
        bt900_central.BT900_GATTC_OPEN)
    common_lib.check_bt900_response(response[0])

    # bt900 enable notifications
    response = bt900_central.send_and_wait_for_response(
        bt900_central.BT900_ENABLE_CYSPP_NOT)
    common_lib.check_bt900_response(response[0])

    # IF820 Event (Text Info contains "W" for gatts data written)
    logging.info("Wait for IF820 Gatts Data Written Event.")
    response = if820_board_p.p_uart.wait_event(
        event=if820_board_p.p_uart.EVENT_GATTS_DATA_WRITTEN, rxtimeout=3)
    common_lib.check_if820_response(
        if820_board_p.p_uart.EVENT_GATTS_DATA_WRITTEN, response)

    time.sleep(1)

    # The two devices are connected.  We can now send data on CYSPP.
    # For the IF820 we need to close the ez_serial port instance and
    # then open a base serial port so we can send raw data with no processing.
    if820_board_p.p_uart.close()
    sp_peripheral = serial_port.SerialPort()
    result = sp_peripheral.open(
        if820_board_p.puart_port_name, if820_board_p.p_uart.IF820_DEFAULT_BAUD)

    # send data from IF820 -> BT900
    for c in CYSPP_DATA:
        sp_peripheral.send(c)
        time.sleep(0.02)
    rx_data = bt900_central.device.get_rx_queue()
    string_utf8 = bytes(rx_data).decode('utf-8')
    logging.info(f"IF820->BT900 Data = {string_utf8}")

    # send data from BT900 -> IF820
    bt900_central.device.send(
        bt900_central.BT900_CYSPP_WRITE_DATA_STRING + CYSPP_DATA + bt900_central.CR)
    time.sleep(0.5)
    rx_data = sp_peripheral.get_rx_queue()
    string_utf8 = bytes(rx_data).decode('utf-8')
    logging.info(f"BT900->IF820 Data = {string_utf8}")

    logging.info("Success!  Cleaning up...")
    # End SPP Mode on both devices, and close open connections.
    if820_board_p.close_ports_and_reset()
    bt900_central.device.send(bt900_central.BT900_SPP_DISCONNECT)
    time.sleep(0.5)
    bt900_central.device.send(bt900_central.BT900_EXIT)
    time.sleep(0.5)
    bt900_central.device.close()
    logging.info("Done!")
