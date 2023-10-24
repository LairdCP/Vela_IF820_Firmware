#!/usr/bin/env python3

import logging
import argparse
import time
import sys
import sys
sys.path.append('./common_lib')
from common_lib.If820Board import If820Board
from common_lib.ezserial_host_api.ezslib import Packet
import common_lib.SerialPort as serial_port
import common_lib.EzSerialPort as ez_port

"""
Hardware Setup
This sample requires the following hardware:
-IF820 connected to PC via USB to act as a Bluetooth Peripheral
-IF820 connected to PC via USB to act as a Bluetooth Central
-P27 is the "Connection" indicator.  On the Laird Module this is pin 33 of the module, attached to GPIO_21 of the pico probe.
-The jumper on J3 CP_ROLE must be placed.
"""
SCAN_MODE_GENERAL_DISCOVERY = ez_port.GapScanMode.NA.value
SCAN_FILTER_ACCEPT_ALL = ez_port.GapScanFilter.NA.value
CY_SPP_DATA = "abcdefghijklmnop"
CENTRAL_ROLE = 1
ENABLE_PLUS_AUTO_START = 2
CYSPP_RX_FLOW_CNTRL = 2
"""
There are two ways to set a device as a central.
Method 1:  GPIO
Method 2:  API Command
If using the API command method, additional api commands are required to connect to a device.
"""
GPIO_MODE = False

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
    If820Board.check_if820_response(if820_board_p.p_uart.CMD_PING, ez_rsp)
    ez_rsp = if820_board_c.p_uart.send_and_wait(if820_board_c.p_uart.CMD_PING)
    If820Board.check_if820_response(if820_board_c.p_uart.CMD_PING, ez_rsp)

    # if820 get mac address of peripheral
    ez_rsp = if820_board_p.p_uart.send_and_wait(
        command=if820_board_p.p_uart.CMD_GET_BT_ADDR)
    If820Board.check_if820_response(
        if820_board_p.p_uart.CMD_GET_BT_ADDR, ez_rsp)
    peripheral_addr = ez_rsp[1].payload.address
    logging.info(ez_rsp[1].payload.address)

    if GPIO_MODE:
        # Set Central CY_ROLE pin low to boot in central mode
        if820_board_c.probe.gpio_to_output(if820_board_c.CP_ROLE)
        if820_board_c.probe.gpio_to_output_low(if820_board_c.CP_ROLE)
        if820_board_c.p_uart.send_and_wait(if820_board_c.p_uart.CMD_REBOOT)

        wait_for_conn = True
        while (wait_for_conn):
            ez_rsp = if820_board_c.p_uart.wait_event(
                if820_board_c.p_uart.EVENT_P_CYSPP_STATUS)
            logging.info(ez_rsp)
            if ez_rsp[1].payload.status == 53:
                wait_for_conn = False

    else:
        # Get device into central mode using api.
        ez_rsp = if820_board_c.p_uart.send_and_wait(command=if820_board_c.p_uart.CMD_P_CYSPP_SET_PARAMETERS,
                                                    apiformat=Packet.EZS_API_FORMAT_TEXT,
                                                    enable=ENABLE_PLUS_AUTO_START,
                                                    role=CENTRAL_ROLE,
                                                    company=305,
                                                    local_key=0,
                                                    remote_key=0,
                                                    remote_mask=0,
                                                    sleep_level=0,
                                                    server_security=0,
                                                    client_flags=CYSPP_RX_FLOW_CNTRL)
        If820Board.check_if820_response(
            if820_board_c.p_uart.CMD_P_CYSPP_SET_PARAMETERS, ez_rsp)

        ez_rsp = if820_board_c.p_uart.send_and_wait(if820_board_c.p_uart.CMD_GAP_START_SCAN,
                                                    mode=SCAN_MODE_GENERAL_DISCOVERY,
                                                    interval=0x400,
                                                    window=0x400,
                                                    active=0,
                                                    filter=SCAN_FILTER_ACCEPT_ALL,
                                                    nodupe=1,
                                                    timeout=5)
        If820Board.check_if820_response(
            if820_board_c.p_uart.CMD_GAP_START_SCAN, ez_rsp)

        while True:
            ez_rsp = if820_board_c.p_uart.wait_event(
                if820_board_c.p_uart.EVENT_GAP_SCAN_RESULT)
            If820Board.check_if820_response(
                if820_board_c.p_uart.EVENT_GAP_SCAN_RESULT, ez_rsp)
            packet = ez_rsp[1]
            logging.debug(f'Received {packet}')
            received_addr = packet.payload.address
            address_type = packet.payload.address_type
            if received_addr == peripheral_addr:
                break
            else:
                logging.debug(f'Not looking for {received_addr}')

        ez_rsp = if820_board_c.p_uart.send_and_wait(
            if820_board_c.p_uart.CMD_GAP_STOP_SCAN)
        If820Board.check_if820_response(
            if820_board_c.p_uart.CMD_GAP_STOP_SCAN, ez_rsp)

        ez_rsp = if820_board_c.p_uart.send_and_wait(if820_board_c.p_uart.CMD_GAP_CONNECT,
                                                    address=received_addr,
                                                    type=address_type,
                                                    interval=6,
                                                    slave_latency=0,
                                                    supervision_timeout=100,
                                                    scan_interval=0x0100,
                                                    scan_window=0x0100,
                                                    scan_timeout=0)
        If820Board.check_if820_response(
            if820_board_c.p_uart.CMD_GAP_CONNECT, ez_rsp)

        logging.info('Found peripheral device, connecting...')
        res = if820_board_c.p_uart.wait_event(
            if820_board_c.p_uart.EVENT_GAP_CONNECTED)
        If820Board.check_if820_response(
            if820_board_c.p_uart.EVENT_GAP_CONNECTED, ez_rsp)
        logging.info('Connected!')
        # time for cyspp to be setup
        time.sleep(2)

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
    for c in CY_SPP_DATA:
        sp_central.send(c)
        time.sleep(0.02)
    # wait 1 sec to ensure all data is sent and received
    time.sleep(1)
    rx_data = sp_peripheral.get_rx_queue()
    string_utf8 = bytes(rx_data).decode('utf-8')
    logging.debug(
        f"Received CYSPP Data Central->Peripheral: {string_utf8}")
    if (len(string_utf8) == 0):
        sys.exit(f"Error!  No data received over CYSPP.")

     # send data from peripheral to central
    for c in CY_SPP_DATA:
        sp_peripheral.send(c)
        time.sleep(0.02)
    # wait 1 sec to ensure all data is sent and received
    time.sleep(1)
    rx_data = sp_central.get_rx_queue()
    string_utf8 = bytes(rx_data).decode('utf-8', 'replace')
    logging.debug(
        f"Received CYSPP Data Peripheral->Central: {string_utf8}")
    if (len(string_utf8) == 0):
        sys.exit(f"Error!  No data received over CYSPP.")

    logging.info("Success!  Cleaning up...")
    # clean everything up
    if820_board_p.close_ports_and_reset()
    if820_board_c.close_ports_and_reset()
    # close the open com ports
    sp_peripheral.close()
    sp_central.close()
    logging.info("Done!")
