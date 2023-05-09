#!/usr/bin/env python3

import argparse
import logging

import common.HciProgrammer as programmer

LOG_MODULE_HCI_PORT = 'hci_port'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--connection',
                        required=True, help="COM port to use")
    parser.add_argument('-b', '--baud', type=int,
                        required=True, help="Initial baud rate to start communication")
    parser.add_argument('-m', '--minidriver',
                        required=True, help="minidriver hex file")
    parser.add_argument('-f', '--file',
                        required=True, help="hex file to program")
    parser.add_argument('-d', '--debug', action='store_true',
                        help="Enable verbose debug messages")
    parser.add_argument('--flash_baud', type=int, default=3000000,
                        help="Baud rate used to flash firmware")

    logging.basicConfig(
        format='%(asctime)s | %(name)s | %(levelname)s | %(message)s', level=logging.INFO)
    args, unknown = parser.parse_known_args()
    if args.debug:
        logging.info("Debugging mode enabled")
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.info("Debugging mode disabled")

    mini_driver = args.minidriver
    com_port = args.connection
    baud = args.baud
    firmware = args.file
    flash_baud = args.flash_baud

    p = programmer.HciProgrammer(mini_driver, com_port, baud)
    if args.debug:
        logging.getLogger(LOG_MODULE_HCI_PORT).setLevel(logging.DEBUG)
    p.program_firmware(flash_baud, firmware)
