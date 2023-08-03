#!/usr/bin/env python

import argparse
import logging
import time
import sys
import ezserial_host_api.ezslib as ez_serial
import common.EzSerialPort as ez_port
from common.If820Board import If820Board

"""
Hardware Setup
This sample requires the following hardware:
-IF820 connected to PC via USB
-Jumpers on PUART_TXD, PUART_RXD must be installed.
"""


def log_resp_err(resp: int):
    if resp != 0:
        logging.error(f'Response err: {resp}')


def quit_on_resp_err(resp: int):
    if resp != 0:
        sys.exit(f'Response err: {resp}')


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

    board = If820Board.get_board()
    logging.info(f'Port Name: {board.puart_port}')

    ezp = ez_port.EzSerialPort()
    open_result = ezp.open(board.puart_port, ezp.IF820_DEFAULT_BAUD)
    if (not open_result):
        raise Exception(
            f"Error!  Unable to open ez_peripheral at {board.puart_port}")

    while (True):
        try:
            logging.info('Send reboot')
            log_resp_err(ezp.send_and_wait(ezp.CMD_REBOOT))
            logging.info('Wait for boot...')
            res = ezp.wait_event(ezp.EVENT_SYSTEM_BOOT)
            if (res[0] == 0):
                logging.info(f'Event: {res[1]}')
            else:
                logging.error(f'Error waiting for boot: {res[0]}')
        except Exception as e:
            logging.error(e)
            ezp.reset()
            ezp.port.reset_input_buffer()
            ezp.clear_rx_queue()
        time.sleep(5)
