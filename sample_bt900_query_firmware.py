#!/usr/bin/env python3

import argparse
import logging
from common.BT900SerialPort import BT900SerialPort

"""
Hardware Setup
This sample requires the following hardware:
-BT900 connected to PC via USB.
"""

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--connection',
                        required=True, help="COM port to use")
    parser.add_argument('-d', '--debug', action='store_true',
                        help="Enable verbose debug messages")
    logging.basicConfig(format='%(asctime)s: %(message)s', level=logging.INFO)
    args, unknown = parser.parse_known_args()
    if args.debug:
        logging.info("Debugging mode enabled")
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.info("Debugging mode disabled")

    bt900 = BT900SerialPort()
    result = bt900.device.open(portName=args.connection, baud=115200)
    if (result):
        response = bt900.get_bt900_fw_ver()
        logging.info(response)
        bt900.device.clear_rx_queue()
        bt900.device.close()
