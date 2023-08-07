#!/usr/bin/env python3

import argparse
import logging
import time
import common.SerialPort as serial_port
from common.BT900SerialPort import BT900SerialPort
from common.CommonLib import CommonLib
from ezserial_host_api.ezslib import Packet
from common.If820Board import If820Board

"""
Hardware Setup
This sample requires the following hardware:
-BT900 connected to PC via USB to act as a Bluetooth Peripheral
-IF820 connected to PC via USB to act as a Bluetooth Central
"""

SPP_DATA = "abcdefghijklmnop"

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-cp', '--connection_p',
                        required=True, help="BT900 Peripheral COM port")
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
    bt900_peripheral = BT900SerialPort()
    open_result = bt900_peripheral.device.open(
        args.connection_p, bt900_peripheral.BT900_DEFAULT_BAUD)
    if (not open_result):
        raise Exception(
            f"Error!  Unable to open bt900 peripheral at {args.connection_p}")

    # IF820
    if820_board_c = If820Board.get_board()
    logging.info(f'Port Name: {if820_board_c.puart_port_name}')
    if820_board_c.open_and_init_board()
    if820_board_c.p_uart.set_queue_timeout(2)

    # bt900 query firmware version
    response = bt900_peripheral.get_bt900_fw_ver()
    logging.info(f"BT900 firmware version = {response}")

    # factory reset if820
    ez_rsp = if820_board_c.p_uart.send_and_wait(
        if820_board_c.p_uart.CMD_FACTORY_RESET)
    common_lib.check_if820_response(
        if820_board_c.p_uart.CMD_FACTORY_RESET, ez_rsp)
    ez_rsp = if820_board_c.p_uart.wait_event(
        if820_board_c.p_uart.EVENT_SYSTEM_BOOT)
    common_lib.check_if820_response(
        if820_board_c.p_uart.EVENT_SYSTEM_BOOT, ez_rsp)

    # IF820 Ping
    ez_rsp = if820_board_c.p_uart.send_and_wait(if820_board_c.p_uart.CMD_PING)
    common_lib.check_if820_response(if820_board_c.p_uart.CMD_PING, ez_rsp)

    # bt900 get mac address of peripheral
    bt900_mac = bt900_peripheral.get_bt900_bluetooth_mac()
    logging.info(f"BT900 bluetooth mac addr = {bt900_mac}")

    # bt900 enter command mode
    response = bt900_peripheral.send_and_wait_for_response(
        bt900_peripheral.BT900_CMD_MODE)
    common_lib.check_bt900_response(response[0])

    # bt900 delete all previous bonds
    response = bt900_peripheral.send_and_wait_for_response(
        bt900_peripheral.BT900_CMD_BTC_BOND_DEL)
    common_lib.check_bt900_response(response[0])

    # bt900 set io cap
    response = bt900_peripheral.send_and_wait_for_response(
        bt900_peripheral.BT900_CMD_BTC_IOCAP)
    common_lib.check_bt900_response(response[0])

    # bt900 set pairable
    response = bt900_peripheral.send_and_wait_for_response(
        bt900_peripheral.BT900_CMD_SET_BTC_PAIRABLE)
    common_lib.check_bt900_response(response[0])

    # bt900 set connectable
    response = bt900_peripheral.send_and_wait_for_response(
        bt900_peripheral.BT900_CMD_SET_BTC_CONNECTABLE)
    common_lib.check_bt900_response(response[0])

    # bt900 set discoverable
    response = bt900_peripheral.send_and_wait_for_response(
        bt900_peripheral.BT900_CMD_SET_BTC_DISCOVERABLE)
    common_lib.check_bt900_response(response[0])

    # bt900 open spp port
    response = bt900_peripheral.send_and_wait_for_response(
        bt900_peripheral.BT900_CMD_SPP_OPEN)
    common_lib.check_bt900_response(response[0])

    # IF820(central) connect to BT900 (peripheral)
    conn_handle = None
    bt900_mac[1].reverse()
    response = if820_board_c.p_uart.send_and_wait(command=if820_board_c.p_uart.CMD_CONNECT,
                                                  address=bt900_mac[1],
                                                  apiformat=Packet.EZS_API_FORMAT_TEXT,
                                                  type=1)
    common_lib.check_if820_response(
        if820_board_c.p_uart.EVENT_SMP_PASSKEY_DISPLAY_REQUESTED, response)
    conn_handle = response[1]

    # IF820 Event (Text Info contains "P")
    logging.info("Wait for IF820 Pairing Requested Event.")
    response = if820_board_c.p_uart.wait_event(
        event=if820_board_c.p_uart.EVENT_SMP_PAIRING_REQUESTED)
    common_lib.check_if820_response(
        if820_board_c.p_uart.EVENT_SMP_PAIRING_REQUESTED, response)

    # bt900 event (Text Info contains "Pair Req")
    logging.info("Wait for BT900 Pair Request Event.")
    bt900_event = bt900_peripheral.wait_for_response(
        rx_timeout_sec=bt900_peripheral.DEFAULT_WAIT_TIME_SEC)
    common_lib.check_bt900_response(
        bt900_event, bt900_peripheral.BT900_PAIR_REQ)

    # bt900 set pairable (Response is "OK")
    logging.info("Send BT900 Pair Request")
    response = bt900_peripheral.send_and_wait_for_response(
        bt900_peripheral.BT900_CMD_BTC_PAIR_RESPONSE)
    common_lib.check_bt900_response(response[0])

    # IF820 Event (Text Info contains "PR")
    logging.info("Wait for IF820 SMP Pairing Result Event.")
    response = if820_board_c.p_uart.wait_event(
        event=if820_board_c.p_uart.EVENT_SMP_PAIRING_RESULT)
    common_lib.check_if820_response(
        if820_board_c.p_uart.EVENT_SMP_PAIRING_RESULT, response)

    # bt900 event (Text Info contains "Pair Result")
    logging.info("Wait for BT900 SMP Pair Result.")
    bt900_event = bt900_peripheral.wait_for_response(
        rx_timeout_sec=bt900_peripheral.DEFAULT_WAIT_TIME_SEC)
    common_lib.check_bt900_response(
        bt900_event, bt900_peripheral.BT900_PAIR_RESULT)

    # IF820 Event (Text Info contains "ENC")
    logging.info("Wait for IF820 SMP Encryption Status Event.")
    response = if820_board_c.p_uart.wait_event(
        event=if820_board_c.p_uart.EVENT_SMP_ENCRYPTION_STATUS)
    common_lib.check_if820_response(
        if820_board_c.p_uart.EVENT_SMP_PASSKEY_DISPLAY_REQUESTED, response)

    # IF820 Event
    logging.info("Wait for IF820 Bluetooth Connected Event.")
    response = if820_board_c.p_uart.wait_event(
        event=if820_board_c.p_uart.EVENT_BT_CONNECTED)
    common_lib.check_if820_response(
        if820_board_c.p_uart.EVENT_BT_CONNECTED, response)

    # bt900 event
    logging.info("Wait for BT900 SPP Connect Event.")
    bt900_event = bt900_peripheral.wait_for_response(
        rx_timeout_sec=bt900_peripheral.DEFAULT_WAIT_TIME_SEC)
    common_lib.check_bt900_response(
        bt900_event, bt900_peripheral.BT900_SPP_CONNECT)

    # The two devices are connected.  We can now send data on SPP.
    # For the IF820 we need to close the ez_serial port instance and
    # then open a base serial port so we can send raw data with no processing.
    if820_board_c.p_uart.close()
    sp_central = serial_port.SerialPort()
    sp_central.open(if820_board_c.puart_port_name,
                    if820_board_c.p_uart.IF820_DEFAULT_BAUD)

    # send data from IF820 -> BT900
    for c in SPP_DATA:
        sp_central.send(c)
        time.sleep(0.03)
    rx_data = bt900_peripheral.device.get_rx_queue()
    string_utf8 = bytes(rx_data).decode('utf-8')
    logging.info(f"IF820->BT900 Data = {string_utf8}")

    # send data from BT900 -> IF820
    bt900_peripheral.device.send(
        bt900_peripheral.BT900_SPP_WRITE_PREFIX + SPP_DATA + bt900_peripheral.CR)
    time.sleep(0.5)
    rx_data = sp_central.get_rx_queue()
    string_utf8 = bytes(rx_data).decode('utf-8')
    logging.info(f"BT900->IF820 Data = {string_utf8}")

    logging.info("Success!  Cleaning up...")
    # End SPP Mode on both devices, and close open connections.
    if820_board_c.close_ports_and_reset()
    bt900_peripheral.device.send(bt900_peripheral.BT900_SPP_DISCONNECT)
    time.sleep(0.5)
    bt900_peripheral.device.send(bt900_peripheral.BT900_EXIT)
    time.sleep(0.5)
    bt900_peripheral.device.close()
    logging.info("Done!")
