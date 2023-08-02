import argparse
import logging
import common.EzSerialPort as ez_port
from common.If820Board import If820Board

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

    board = If820Board.get_board()
    logging.info(f'Port Name: {board.puart_port}')

    ezp = ez_port.EzSerialPort()
    open_result = ezp.open(board.puart_port, ezp.IF820_DEFAULT_BAUD)
    if (not open_result):
        raise Exception(
            f"Error!  Unable to open ez_peripheral at {board.puart_port}")

    res = ezp.send_and_wait(ezp.CMD_PING)
    if res[0] == 0:
        logging.info(f'Ping result success: {res}')
    else:
        logging.error(f'Ping result error: {res}')
