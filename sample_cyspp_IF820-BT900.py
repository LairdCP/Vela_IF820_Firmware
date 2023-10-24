#!/usr/bin/env python3

import argparse
import logging
import time
import sys
sys.path.append('./common_lib')
from common_lib.BT900SerialPort import BT900SerialPort
from common_lib.ezserial_host_api.ezslib import Packet
from common_lib.If820Board import If820Board

BT900_ADV_FLAGS = bytes([0x02, 0x01, 0x06])
BT900_ADV_NAME = bytes([0x0C, 0x09, 0x4C, 0x41, 0x49,
                       0x52, 0x44, 0x20, 0x42, 0x54, 0x39, 0x30, 0x30])

"""
Hardware Setup
This sample requires the following hardware:
-BT900 connected to PC via USB to act as a Bluetooth Peripheral.  SIO19 must be pulled to ground via jumper.
 *** The BT900 should be reset before the test to ensure it is advertising ***
-IF820 connected to PC via USB to act as a Bluetooth Central.
"""

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-cp', '--connection_p',
                        required=True, help="Peripheral COM port")
    parser.add_argument('-d', '--debug', action='store_true',
                        help="Enable verbose debug messages")
    args, unknown = parser.parse_known_args()
    logging.basicConfig(format='%(asctime)s: %(message)s', level=logging.INFO)
    if args.debug:
        logging.info("Debugging mode enabled")
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.info("Debugging mode disabled")

    # open devices
    # bt900
    bt900_peripheral = BT900SerialPort()
    bt900_peripheral.device.open(
        args.connection_p, bt900_peripheral.BT900_DEFAULT_BAUD)

    # IF820
    if820_board_c = If820Board.get_board()
    logging.info(f'Port Name: {if820_board_c.puart_port_name}')
    if820_board_c.open_and_init_board()

    # IF820 Ping
    ez_rsp = if820_board_c.p_uart.send_and_wait(if820_board_c.p_uart.CMD_PING)
    If820Board.check_if820_response(if820_board_c.p_uart.CMD_PING, ez_rsp)

    # Put into central mode by setting CP_ROLE (GPIO18 low)
    if820_board_c.probe.gpio_to_output(if820_board_c.CP_ROLE)
    if820_board_c.probe.gpio_to_output_low(if820_board_c.CP_ROLE)
    ez_rsp = if820_board_c.p_uart.send_and_wait(
        if820_board_c.p_uart.CMD_REBOOT)
    If820Board.check_if820_response(if820_board_c.p_uart.CMD_REBOOT, ez_rsp)
    ez_rsp = if820_board_c.p_uart.wait_event(
        if820_board_c.p_uart.EVENT_SYSTEM_BOOT)
    If820Board.check_if820_response(
        if820_board_c.p_uart.EVENT_SYSTEM_BOOT, ez_rsp)

    bt900_addr = None
    while (bt900_addr == None):
        ez_rsp = if820_board_c.p_uart.wait_event(
            if820_board_c.p_uart.EVENT_GAP_SCAN_RESULT)
        If820Board.check_if820_response(
            if820_board_c.p_uart.EVENT_GAP_SCAN_RESULT, ez_rsp)
        packet = ez_rsp[1]
        if ((packet.payload.address_type == 0) and
            (packet.payload.data.startswith(BT900_ADV_FLAGS)) and
                (packet.payload.data.endswith(BT900_ADV_NAME))):
            logging.info("BT900 Found!")
            bt900_addr = packet.payload.address
            address_type = packet.payload.address_type
            logging.info(bt900_addr)

    ez_rsp = if820_board_c.p_uart.send_and_wait(
        if820_board_c.p_uart.CMD_GAP_STOP_SCAN)
    If820Board.check_if820_response(
        if820_board_c.p_uart.CMD_GAP_STOP_SCAN, ez_rsp)

    # IF820(central) connect to BT900 (peripheral)
    conn_handle = None
    logging.info("Connecting to peripheral.")
    response = if820_board_c.p_uart.send_and_wait(command=if820_board_c.p_uart.CMD_GAP_CONNECT,
                                                  apiformat=Packet.EZS_API_FORMAT_TEXT,
                                                  address=bt900_addr,
                                                  type=0,
                                                  interval=6,
                                                  slave_latency=address_type,
                                                  supervision_timeout=100,
                                                  scan_interval=0x0100,
                                                  scan_window=0x0100,
                                                  scan_timeout=0)
    If820Board.check_if820_response(
        if820_board_c.p_uart.CMD_GAP_CONNECT, response)
    logging.info("Wait for connected event.")
    ez_rsp = if820_board_c.p_uart.wait_event(
        if820_board_c.p_uart.EVENT_GAP_CONNECTED)
    logging.info("Connected event!")
    conn_handle = ez_rsp[1].payload.conn_handle
    wait_for_rpc = False

    # wait for result events to pour in - we don't need them.
    time.sleep(6)

    # enable notifications on characteristic
    if820_board_c.p_uart.clear_rx_queue()
    ez_rsp = if820_board_c.p_uart.send_and_wait(command=if820_board_c.p_uart.CMD_GATTC_WRITE_HANDLE,
                                                apiformat=Packet.EZS_API_FORMAT_TEXT,
                                                conn_handle=conn_handle,
                                                attr_handle=0x16,
                                                type=0,
                                                data=[0x01, 0x00])
    If820Board.check_if820_response(
        if820_board_c.p_uart.CMD_GATTC_WRITE_HANDLE, ez_rsp)
    time.sleep(0.5)

    # Send data on CYSPP.
    logging.info("Send data on CYSPP")
    ez_rsp = if820_board_c.p_uart.send_and_wait(command=if820_board_c.p_uart.CMD_GATTC_WRITE_HANDLE,
                                                apiformat=Packet.EZS_API_FORMAT_TEXT,
                                                conn_handle=conn_handle,
                                                attr_handle=0x13,
                                                type=1,
                                                data=[0x30, 0x31, 0x32, 0x33, 0x34, 0x35])
    If820Board.check_if820_response(
        if820_board_c.p_uart.CMD_GATTC_WRITE_HANDLE, ez_rsp)

    time.sleep(0.5)
    rx_data = bt900_peripheral.device.get_rx_queue()
    string_utf8 = bytes(rx_data).decode('utf-8')
    logging.info(f"IF820->BT900 Data = {string_utf8}")

    # send data from BT900 -> IF820
    time.sleep(0.5)
    bt900_peripheral.device.send('a')
    ez_rsp = if820_board_c.p_uart.wait_event(
        if820_board_c.p_uart.EVENT_GATTC_DATA_RECEIVED)
    If820Board.check_if820_response(
        if820_board_c.p_uart.EVENT_GATTC_DATA_RECEIVED, ez_rsp)
    rx_data = ez_rsp[1].payload.data
    string_utf8 = bytes(rx_data).decode('utf-8')
    logging.info(f"BT900->IF820 Data = {string_utf8}")

    # End CYSPP Mode on both devices, and close open connections.
    if820_board_c.close_ports_and_reset()
    bt900_peripheral.device.close()
