#!/usr/bin/env python3

"""The advertiser sample configures a peripheral device to advertise a custom
payload and a central device to scan for the peripheral device.
The custom advertisement payload contains a 1 byte counter value that is incremented
every two seconds.
The central device prints the counter value when it receives a new advertisement.
To run this test you need two IF820 DVK boards.
"""

import argparse
import logging
import time
import threading
import sys
sys.path.append('./common_lib')
import common_lib.EzSerialPort as ez_port
from common_lib.If820Board import If820Board

API_FORMAT = 1  # Binary
ADV_MODE = ez_port.GapAdvertMode.NA.value
ADV_TYPE = ez_port.GapAdvertType.UNDIRECTED_HIGH_DUTY_CYCLE.value
ADV_INTERVAL = 0x40
ADV_CHANNELS = ez_port.GapAdvertChannels.CHANNEL_ALL.value
ADV_TIMEOUT = 0
ADV_FLAGS = ez_port.GapAdvertFlags.ALL.value
ADV_DATA = [0x02, 0x01, 0x06, 0x0a, 0x08, 0x6d, 0x79, 0x5f, 0x73, 0x65, 0x6e,
            0x73, 0x6f, 0x72, 0x04, 0xff, 0x77, 0x00, 0x01]
SCAN_MODE = ez_port.GapScanMode.NA.value
SCAN_INTERVAL = 0x40
SCAN_WINDOW = 0x40
SCAN_FILTER_ACCEPT_ALL = ez_port.GapScanFilter.NA.value
PERIPHERAL_ADDRESS = None


def quit_on_resp_err(resp: int):
    """Exit the program if the response code is not 0.

    Args:
        resp (int): response code
    """
    if resp != 0:
        sys.exit(f'Response err: {hex(resp)}')

def scanner_thread():
    """Thread to scan for the peripheral device and print the counter value.
    """
    last_counter = -1
    logging.info('Configure scanner...')
    logging.info(
        f'Scan mode: {SCAN_MODE}, interval: {SCAN_INTERVAL}, window: {SCAN_WINDOW}')
    quit_on_resp_err(if820_board_c.p_uart.send_and_wait(if820_board_c.p_uart.CMD_GAP_START_SCAN,
                                                        mode=SCAN_MODE,
                                                        interval=SCAN_INTERVAL,
                                                        window=SCAN_WINDOW,
                                                        active=0,
                                                        filter=SCAN_FILTER_ACCEPT_ALL,
                                                        nodupe=0,
                                                        timeout=0)[0])
    while True:
        try:
            res = if820_board_c.p_uart.wait_event(
                if820_board_c.p_uart.EVENT_GAP_SCAN_RESULT)
            quit_on_resp_err(res[0])
            packet = res[1]
            logging.debug(f'Received {packet}')
            received_addr = packet.payload.address
            if received_addr == PERIPHERAL_ADDRESS:
                counter = packet.payload.data[-1]
                if counter != last_counter:
                    last_counter = counter
                    logging.info(f'Received value {counter}')
                else:
                    logging.debug('Received duplicate advert')
            else:
                logging.debug(f'Not looking for {received_addr}')
        except Exception as e:
            logging.warning(f'Scanner: {e}')
            if820_board_c.p_uart.close()
            time.sleep(0.5)
            if820_board_c.p_uart.open(
                if820_board_c.puart_port_name, if820_board_c.p_uart.IF820_DEFAULT_BAUD)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true',
                        help="Enable verbose debug messages")
    logging.basicConfig(format='%(asctime)s [%(module)s] %(levelname)s: %(message)s', level=logging.INFO)
    args, unknown = parser.parse_known_args()
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
    boot_info_p = if820_board_p.open_and_init_board()
    boot_info_c = if820_board_c.open_and_init_board()
    if820_board_c.p_uart.set_api_format(API_FORMAT)
    if820_board_p.p_uart.set_api_format(API_FORMAT)
    logging.info(f'Advertiser: {boot_info_p}')
    logging.info(f'Scanner: {boot_info_c}')
    PERIPHERAL_ADDRESS = boot_info_p.payload.address
    threading.Thread(target=scanner_thread,
                     daemon=True).start()

    logging.info('Configure advertiser...')
    quit_on_resp_err(if820_board_p.p_uart.send_and_wait(
        if820_board_p.p_uart.CMD_GAP_STOP_ADV)[0])
    quit_on_resp_err(if820_board_p.p_uart.send_and_wait(if820_board_p.p_uart.CMD_GAP_SET_ADV_PARAMETERS,
                                                        mode=ADV_MODE,
                                                        type=ADV_TYPE,
                                                        channels=ADV_CHANNELS,
                                                        high_interval=ADV_INTERVAL,
                                                        high_duration=ADV_TIMEOUT,
                                                        low_interval=ADV_INTERVAL,
                                                        low_duration=ADV_TIMEOUT,
                                                        flags=ADV_FLAGS,
                                                        directAddr=[
                                                            0, 0, 0, 0, 0, 0],
                                                        directAddrType=ez_port.GapAddressType.PUBLIC.value)[0])
    logging.info(
        f'Advert mode: {ADV_MODE}, type:{ADV_TYPE}, high_interval: {ADV_INTERVAL}, high_duration:{ADV_TIMEOUT}, flags:{ADV_FLAGS}')
    quit_on_resp_err(if820_board_p.p_uart.send_and_wait(if820_board_p.p_uart.CMD_GAP_SET_ADV_DATA,
                                                        data=ADV_DATA)[0])
    quit_on_resp_err(if820_board_p.p_uart.send_and_wait(if820_board_p.p_uart.CMD_GAP_START_ADV,
                                                        mode=ADV_MODE,
                                                        type=ADV_TYPE,
                                                        channels=ADV_CHANNELS,
                                                        high_interval=ADV_INTERVAL,
                                                        high_duration=ADV_TIMEOUT,
                                                        low_interval=ADV_INTERVAL,
                                                        low_duration=ADV_TIMEOUT,
                                                        flags=ADV_FLAGS,
                                                        directAddr=[
                                                            0, 0, 0, 0, 0, 0],
                                                        directAddrType=ez_port.GapAddressType.PUBLIC.value)[0])

    while (True):
        time.sleep(2)
        counter = ADV_DATA[-1]
        counter = counter + 1
        if counter >= 256:
            counter = 0
        ADV_DATA[-1] = counter
        logging.info(f'Advertising value {counter}')
        quit_on_resp_err(if820_board_p.p_uart.send_and_wait(if820_board_p.p_uart.CMD_GAP_SET_ADV_DATA,
                                                            data=ADV_DATA)[0])
