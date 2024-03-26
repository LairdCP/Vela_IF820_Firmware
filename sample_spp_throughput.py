#!/usr/bin/env python3

import logging
import argparse
import time
import sys
import threading
import string
import random
sys.path.append('./common_lib/libraries')
import EzSerialPort as ez_port
from If820Board import If820Board


"""
This sample creates an SPP connection between two IF820 boards and sends data between them.
Data is sent from the Central to the Peripheral and then from the Peripheral to the Central.
Received data is compared to the sent data to ensure data integrity.
Each data chunk sent is randomly generated.

Hardware Setup
This sample requires the following hardware:
-IF820 connected to PC via USB to act as a Bluetooth Peripheral
-IF820 connected to PC via USB to act as a Bluetooth Central
NOTE: The DVK Probe (RP2040) v1.3.0, or earlier, firmware has two bugs that prevent this
sample from working:
- The UART flow control is not working correctly
- RX bytes can be dropped.
New firmware is available to fix these issues.
"""

API_FORMAT = ez_port.EzSerialApiMode.TEXT.value
UART_BITS_PER_BYTE = 10
# UART baud rate to use for the test.
# This baud rate is only set for this session and not saved to flash.
BAUD_RATE = 1000000
# UART flow control is used for the test. It is required to prevent data loss. Set to 0 at your own risk
FLOW_CONTROL = 1
# How long to run the throughput test for.
THROUGHPUT_TEST_TIMEOUT_SECS = 10
# Length of the data chunk to send. This is the size of each chuck written in the send loop.
# To Achieve maximum throughput, this should be set to greater than or equal to the number of bytes
# that can be sent in one send loop iteration. For example:
# SEND_DATA_CHUNK_LEN = THROUGHPUT_TEST_TIMEOUT_SECS * BAUD_RATE / UART_BITS_PER_BYTE
SEND_DATA_CHUNK_LEN = THROUGHPUT_TEST_TIMEOUT_SECS * BAUD_RATE / UART_BITS_PER_BYTE
# How long to wait for data to be received. This is used to determine when RX is finished.
RX_TIMEOUT_SECS = 1

rx_done_event = None
data_sent = []
data_received = []
tx_start_time = 0


def factory_reset(board: If820Board):
    logging.info("IF820 Factory Reset")
    ez_rsp = board.p_uart.send_and_wait(
        board.p_uart.CMD_FACTORY_RESET)
    If820Board.check_if820_response(
        board.p_uart.CMD_FACTORY_RESET, ez_rsp)
    logging.info("Wait for IF820 Reboot...")
    ez_rsp = board.p_uart.wait_event(
        board.p_uart.EVENT_SYSTEM_BOOT)
    If820Board.check_if820_response(
        board.p_uart.EVENT_SYSTEM_BOOT, ez_rsp)
    ez_rsp = board.p_uart.wait_event(
        board.p_uart.EVENT_GAP_ADV_STATE_CHANGED)
    If820Board.check_if820_response(
        board.p_uart.EVENT_GAP_ADV_STATE_CHANGED, ez_rsp)


def wait_for_connection(board: If820Board):
    ez_rsp = board.p_uart.wait_event(
        board.p_uart.EVENT_BT_CONNECTED)
    If820Board.check_if820_response(
        board.p_uart.EVENT_BT_CONNECTED, ez_rsp)


def send_receive_data(sender: If820Board, receiver: If820Board):
    global data_sent, rx_done_event, tx_start_time
    receiver.p_uart.clear_rx_queue()
    rx_thread = threading.Thread(target=lambda: __receive_data_thread(receiver),
                                 daemon=True)
    rx_done_event = threading.Event()
    rx_thread.start()
    logging.info(
        f"Start sending data for at least {THROUGHPUT_TEST_TIMEOUT_SECS} seconds...")
    data_sent = []
    packet_num = 0
    tx_start_time = time.time()
    while (time.time() - tx_start_time) < THROUGHPUT_TEST_TIMEOUT_SECS:
        send = bytearray(''.join(random.choices(string.ascii_letters +
                                                string.digits, k=int(SEND_DATA_CHUNK_LEN))), 'utf-8')
        # Add a packet header that contains the packet number
        # This is useful for identifying the packet when looking at UART logic traces
        header = packet_num.to_bytes(4, byteorder='little')
        send[:4] = header
        send = bytes(send)
        sender.p_uart.send(send)
        data_sent.extend(list(send))
        packet_num += 1

    logging.info(f"Sent {len(data_sent)} bytes, Wait for data to be received...")
    if not rx_done_event.wait(THROUGHPUT_TEST_TIMEOUT_SECS * 2):
        logging.error("Timeout waiting for data to be received")


def __receive_data_thread(receiver: If820Board):
    global data_sent, data_received, rx_done_event, tx_start_time
    last_rx_time = time.time()
    logging.info("Start receiving data...")
    data_received = []
    while time.time() - last_rx_time < RX_TIMEOUT_SECS:
        rx_data = receiver.p_uart.read()
        if len(rx_data) > 0:
            last_rx_time = time.time()
            data_received.extend(list(rx_data))
    logging.info(f"All data received! Received {len(data_received)} bytes")
    if data_received != data_sent:
        logging.error(
            f"\r\n\r\nData received does not match data sent!\r\n")
        for index, (txd, rxd) in enumerate(zip(data_sent, data_received)):
            if txd != rxd:
                print(
                    f"RX mismatch at index: {index} (packet {hex(int(index/SEND_DATA_CHUNK_LEN))}), val: {hex(rxd)}")
                print(
                    f"tx[{index}]: {hex(data_sent[index])}, tx[{index + 1}]: {hex(data_sent[index + 1])}, tx[{index + 2}]: {hex(data_sent[index + 2])}")
                print(
                    f"rx[{index}]: {hex(data_received[index])}, rx[{index + 1}]: {hex(data_received[index + 1])}")
                data_received.insert(index, data_sent[index])
    bytes_per_sec = len(data_received) / (last_rx_time - tx_start_time)
    logging.info(
        f"Total TX -> RX time: {last_rx_time - tx_start_time:.1f} Throughput: {bytes_per_sec:.2f} Bps ({bytes_per_sec * 8:.2f} bps)")
    rx_done_event.set()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true',
                        help="Enable verbose debug messages")
    args, unknown = parser.parse_known_args()
    logging.basicConfig(
        format='%(asctime)s [%(module)s] %(levelname)s: %(message)s', level=logging.INFO)
    if args.debug:
        logging.info("Debugging mode enabled")
        logging.getLogger().setLevel(logging.DEBUG)

    boards = If820Board.get_connected_boards()
    if len(boards) < 2:
        logging.critical(
            "Two IF820 boards required for this sample.")
        exit(1)

    if820_board_c = boards[0]
    if820_board_p = boards[1]
    if820_board_c.open_and_init_board()
    if820_board_p.open_and_init_board()
    if820_board_c.p_uart.set_api_format(API_FORMAT)
    if820_board_p.p_uart.set_api_format(API_FORMAT)

    factory_reset(if820_board_c)
    factory_reset(if820_board_p)

    logging.info(f"Set UART baud {BAUD_RATE} flow control {FLOW_CONTROL}")
    ez_rsp = if820_board_c.p_uart.send_and_wait(if820_board_c.p_uart.CMD_SET_UART_PARAMS,
                                                baud=BAUD_RATE,
                                                autobaud=0,
                                                autocorrect=0,
                                                flow=FLOW_CONTROL,
                                                databits=8,
                                                parity=0,
                                                stopbits=1,
                                                uart_type=0)
    If820Board.check_if820_response(
        if820_board_c.p_uart.CMD_SET_UART_PARAMS, ez_rsp)
    ez_rsp = if820_board_p.p_uart.send_and_wait(if820_board_p.p_uart.CMD_SET_UART_PARAMS,
                                                baud=BAUD_RATE,
                                                autobaud=0,
                                                autocorrect=0,
                                                flow=FLOW_CONTROL,
                                                databits=8,
                                                parity=0,
                                                stopbits=1,
                                                uart_type=0)
    If820Board.check_if820_response(
        if820_board_p.p_uart.CMD_SET_UART_PARAMS, ez_rsp)

    if820_board_c.reconfig_puart(BAUD_RATE)
    if820_board_p.reconfig_puart(BAUD_RATE)
    if820_board_c.p_uart.set_api_format(API_FORMAT)
    if820_board_p.p_uart.set_api_format(API_FORMAT)

    # Wait for the module to change its UART params
    time.sleep(0.1)

    logging.info("Get Peripheral BT MAC")
    peripheral_bt_mac = None
    ez_rsp = if820_board_p.p_uart.send_and_wait(
        if820_board_p.p_uart.CMD_GET_BT_ADDR)
    If820Board.check_if820_response(
        if820_board_p.p_uart.CMD_GET_BT_ADDR, ez_rsp)
    peripheral_bt_mac = ez_rsp[1].payload.address

    logging.info("Connect to Peripheral")
    ez_rsp = if820_board_c.p_uart.send_and_wait(if820_board_c.p_uart.CMD_CONNECT,
                                                address=peripheral_bt_mac,
                                                type=1)
    If820Board.check_if820_response(if820_board_p.p_uart.CMD_CONNECT, ez_rsp)
    logging.info("Wait for central connection...")
    wait_for_connection(if820_board_c)
    logging.info("Wait for peripheral connection...")
    wait_for_connection(if820_board_p)

    logging.info("Send data from Central to Peripheral")
    send_receive_data(if820_board_c, if820_board_p)
    logging.info("Send data from Peripheral to Central")
    send_receive_data(if820_board_p, if820_board_c)

    logging.info("Data exchanged! Reset the boards...")
    if820_board_p.close_ports_and_reset()
    if820_board_c.close_ports_and_reset()
    logging.info("Done!")
