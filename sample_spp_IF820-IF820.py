#!/usr/bin/env python3
import logging
import argparse
import time
import sys
sys.path.append('./common_lib')
import common_lib.SerialPort as serial_port
from common_lib.CommonLib import CommonLib
from common_lib.If820Board import If820Board

"""
Hardware Setup
This sample requires the following hardware:
-IF820 connected to PC via USB to act as a Bluetooth Peripheral
-IF820 connected to PC via USB to act as a Bluetooth Central
"""

FLAG_INQUIRY_NAME = 1
SPP_DATA = "abcdefghijklmnop"

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
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

    boards = If820Board.get_connected_boards()
    if len(boards) < 2:
        logging.critical(
            "Two IF820 boards required for this sample.")
        exit(1)

    if820_board_p = boards[0]
    if820_board_c = boards[1]
    if820_board_p.open_and_init_board()
    if820_board_c.open_and_init_board()

    # Send Ping just to verify coms before proceeding
    ez_rsp = if820_board_p.p_uart.send_and_wait(if820_board_p.p_uart.CMD_PING)
    common_lib.check_if820_response(if820_board_p.p_uart.CMD_PING, ez_rsp)
    ez_rsp = if820_board_c.p_uart.send_and_wait(if820_board_p.p_uart.CMD_PING)
    common_lib.check_if820_response(if820_board_c.p_uart.CMD_PING, ez_rsp)

    # Query the peripheral to get is Bluetooth Address
    peripheral_bt_mac = None
    ez_rsp = if820_board_p.p_uart.send_and_wait(
        if820_board_p.p_uart.CMD_GET_BT_ADDR)
    common_lib.check_if820_response(
        if820_board_p.p_uart.CMD_GET_BT_ADDR, ez_rsp)
    peripheral_bt_mac = ez_rsp[1].payload.address
    logging.debug(peripheral_bt_mac)

    # Command Central to connect to Peripheral
    conn_handle = None
    ez_rsp = if820_board_c.p_uart.send_and_wait(if820_board_c.p_uart.CMD_CONNECT,
                                                address=peripheral_bt_mac,
                                                type=1)
    common_lib.check_if820_response(if820_board_p.p_uart.CMD_CONNECT, ez_rsp)
    conn_handle = ez_rsp[1].payload.conn_handle

    ez_rsp = if820_board_c.p_uart.wait_event(
        if820_board_c.p_uart.EVENT_BT_CONNECTED)
    common_lib.check_if820_response(
        if820_board_c.p_uart.EVENT_BT_CONNECTED, ez_rsp)

    # close ez serial ports
    if820_board_p.p_uart.close()
    if820_board_c.p_uart.close()

    # open serial ports
    sp_peripheral = serial_port.SerialPort()
    sp_central = serial_port.SerialPort()
    sp_peripheral.open(if820_board_p.puart_port_name,
                       if820_board_p.p_uart.IF820_DEFAULT_BAUD)
    sp_central.open(if820_board_c.puart_port_name,
                    if820_board_c.p_uart.IF820_DEFAULT_BAUD)

    # send data from central to peripheral
    for c in SPP_DATA:
        sp_central.send(c)
        time.sleep(0.02)
    # wait 1 sec to ensure all data is sent and received
    time.sleep(1)
    rx_data = sp_peripheral.get_rx_queue()
    string_utf8 = bytes(rx_data).decode('utf-8')
    logging.debug(
        f"Received SPP Data Central->Peripheral: {string_utf8}")
    if (len(string_utf8) == 0):
        sys.exit(f"Error!  No data received over SPP.")

    # send data from peripheral to central
    for c in SPP_DATA:
        sp_peripheral.send(c)
        time.sleep(0.02)
    # wait 1 sec to ensure all data is sent and received
    time.sleep(1)
    rx_data = sp_central.get_rx_queue()
    string_utf8 = bytes(rx_data).decode('utf-8')
    logging.debug(
        f"Received SPP Data Peripheral->Central: {string_utf8}")
    if (len(string_utf8) == 0):
        sys.exit(f"Error!  No data received over SPP.")

    logging.info("Success!  Cleaning up...")
    # clean everything up
    # disable spp mode by changing state of P13 of IF820
    if820_board_p.close_ports_and_reset()
    if820_board_c.close_ports_and_reset()
    # close the open com ports
    sp_peripheral.close()
    sp_central.close()
    logging.info("Done!")
