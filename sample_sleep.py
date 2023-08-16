#!/usr/bin/env python3

import logging
import argparse
import time
from common.CommonLib import CommonLib
from ezserial_host_api.ezslib import Packet
from common.If820Board import If820Board

# GPIO20 is LP_MODE I/O Control
# LOW_POWER_ENABLE = 0
# LOW_POWER_DISABLE = 1

# GPIO16 is DEV_WAKE I/O Control
# DEV_WAKE_ENABLE = 1
# DEV_WAKE_DISABLE = 0

SYS_DEEP_SLEEP_LEVEL = 2
HIBERNATE = False
SLEEP_TIME = 15

"""
Hardware Setup
This sample requires the following hardware:
-IF820 connected to PC via USB to act as a Bluetooth Peripheral
-Jumpers on PUART_TXD, PUART_RXD, LP_MODE, and BT_DEV_WAKE must be installed.
-Depending on how current is measured on the dev board, it maybe necessary to remove
 the above jumpers after the device enters sleep mode to avoid I/O leakage.
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

    common_lib = CommonLib()

    # Disable sleep via gpio
    if820_board_p.probe.gpio_to_output(if820_board_p.probe.GPIO_20)
    if820_board_p.probe.gpio_to_output_high(if820_board_p.probe.GPIO_20)

    # Allow the device some time to wake from sleep
    time.sleep(0.5)

    # Send Ping just to verify coms before proceeding
    ez_rsp = if820_board_p.p_uart.send_and_wait(
        if820_board_p.p_uart.CMD_PING)
    common_lib.check_if820_response(if820_board_p.p_uart.CMD_PING, ez_rsp)

    if HIBERNATE:
        # set hibernate mode
        ez_rsp = if820_board_p.p_uart.send_and_wait(command=if820_board_p.p_uart.CMD_SET_SLEEP_PARAMS,
                                                    apiformat=Packet.EZS_API_FORMAT_TEXT, level=SYS_DEEP_SLEEP_LEVEL, hid_off_sleep_time=0)
        common_lib.check_if820_response(
            if820_board_p.p_uart.CMD_SET_SLEEP_PARAMS, ez_rsp)

    else:
        # turn off bluetooth
        ez_rsp = if820_board_p.p_uart.send_and_wait(
            if820_board_p.p_uart.CMD_GAP_STOP_ADV)
        common_lib.check_if820_response(
            if820_board_p.p_uart.CMD_GAP_STOP_ADV, ez_rsp)

        ez_rsp = if820_board_p.p_uart.send_and_wait(
            if820_board_p.p_uart.CMD_SET_PARAMS,
            apiformat=Packet.EZS_API_FORMAT_TEXT,
            link_super_time_out=0x7d00,
            discoverable=0,
            connectable=0,
            flags=0,
            scn=0,
            active_bt_discoverability=0,
            active_bt_connectability=0)
        common_lib.check_if820_response(
            if820_board_p.p_uart.CMD_SET_PARAMS, ez_rsp)

    # Enable Sleep via GPIO
    logging.info("Put device to sleep.")
    if820_board_p.probe.gpio_to_output_low(if820_board_p.probe.GPIO_20)

    # Device will now sleep until awoken by the host.
    # This code can be commented out to keep the device sleeping.
    time.sleep(SLEEP_TIME)
    logging.info("Wake the device.")
    if820_board_p.probe.gpio_to_output_high(if820_board_p.probe.GPIO_20)

    if HIBERNATE:
        # device will reboot when waking up from hibernate
        ez_rsp = if820_board_p.p_uart.wait_event(
            if820_board_p.p_uart.EVENT_SYSTEM_BOOT)
    else:
        # Wait for module to wake up
        time.sleep(0.5)

    # Send Ping just to verify coms before proceeding
    ez_rsp = if820_board_p.p_uart.send_and_wait(
        if820_board_p.p_uart.CMD_PING)
    common_lib.check_if820_response(if820_board_p.p_uart.CMD_PING, ez_rsp)

    # Close the open com ports
    if820_board_p.close_ports_and_reset()
