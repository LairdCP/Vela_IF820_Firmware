#!/usr/bin/env python3

import argparse
import logging
import sys
sys.path.append('./common_lib')
from common_lib.If820Board import If820Board

"""
Hardware Setup
This sample requires the following hardware:
-IF820 connected to PC via USB
-Jumpers on PUART_TXD, PUART_RXD must be installed.
"""

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true',
                        help="Enable verbose debug messages")
    logging.basicConfig(format='%(asctime)s: %(message)s', level=logging.INFO)
    args, unknown = parser.parse_known_args()
    if args.debug:
        logging.info("Debugging mode enabled")
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.info("Debugging mode disabled")

    if820_board_p = If820Board.get_board()
    logging.info(f'Port Name: {if820_board_p.puart_port_name}')
    if820_board_p.open_and_init_board()

    res = if820_board_p.p_uart.send_and_wait(if820_board_p.p_uart.CMD_PING)
    if res[0] == 0:
        logging.info(f'Ping result success: {res}')
    else:
        logging.error(f'Ping result error: {res}')
