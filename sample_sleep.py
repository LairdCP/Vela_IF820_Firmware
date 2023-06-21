#!/usr/bin/env python3

import argparse
import time
import sys
import common.EzSerialPort as ez_port
import common.SerialPort as serial_port
import common.PicoProbe as pico_probe
from common.CommonLib import CommonLib
from common.AppLogging import AppLogging
from ezserial_host_api.ezslib import Packet

# GPIO20 is LP_MODE I/O Control
# LOW_POWER_ENABLE = 0
# LOW_POWER_DISABLE = 1

# GPIO16 is DEV_WAKE I/O Control
# DEV_WAKE_ENABLE = 1
# DEV_WAKE_DISABLE = 0

SYS_DEEP_SLEEP_LEVEL = 2

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
    parser.add_argument('-cp', '--connection_p',
                        required=True, help="Peripheral COM port")
    parser.add_argument('-ppp', '--picoprobe_p',
                        required=True, help="Pico Probe Id Perhipheral")
    parser.add_argument('-d', '--debug', action='store_true',
                        help="Enable verbose debug messages")
    args, unknown = parser.parse_known_args()
    app_logger = AppLogging("sleep sample")
    if args.debug:
        app_logger.configure_app_logging(
            level=app_logger.DEBUG, file_level=app_logger.NOTSET)
        app_logger.app_log_info("Debugging mode enabled")

    common_lib = CommonLib()

    ezp_peripheral = ez_port.EzSerialPort()
    open_result = ezp_peripheral.open(
        args.connection_p, ezp_peripheral.IF820_DEFAULT_BAUD)
    if (not open_result[1]):
        raise Exception(
            f"Error!  Unable to open ez_peripheral at {args.connection_p}")

    pp_peripheral = pico_probe.PicoProbe()
    pp_peripheral.open(args.picoprobe_p)
    if (not pp_peripheral.is_open):
        app_logger.app_log_critical("Unable to open Pico Probe.")

    # Disable sleep via gpio
    pp_peripheral.gpio_to_output(pp_peripheral.GPIO_20)
    pp_peripheral.gpio_to_output_high(pp_peripheral.GPIO_20)

    # DEV_WAKE
    pp_peripheral.gpio_to_output(pp_peripheral.GPIO_16)
    pp_peripheral.gpio_to_output_high(pp_peripheral.GPIO_16)

    # Allow the device some time to wake from sleep
    time.sleep(1)

    # Send Ping just to verify coms before proceeding
    ez_rsp = ezp_peripheral.send_and_wait(ezp_peripheral.CMD_PING)
    common_lib.check_if820_response(ezp_peripheral.CMD_PING, ez_rsp)

    # Factory Reset Peripheral
    app_logger.app_log_info("Factory reset device.")
    ezp_peripheral.send_and_wait(ezp_peripheral.CMD_FACTORY_RESET)
    common_lib.check_if820_response(ezp_peripheral.CMD_FACTORY_RESET, ez_rsp)
    ez_rsp = ezp_peripheral.wait_event(ezp_peripheral.EVENT_SYSTEM_BOOT)
    common_lib.check_if820_response(ezp_peripheral.EVENT_SYSTEM_BOOT, ez_rsp)

    # Enable Deep Sleep via System Command
    app_logger.app_log_info("Enable deep sleep via system command.")
    ez_rsp = ezp_peripheral.send_and_wait(command=ezp_peripheral.CMD_SET_SLEEP_PARAMS,
                                          apiformat=Packet.EZS_API_FORMAT_TEXT, level=SYS_DEEP_SLEEP_LEVEL, hid_off_sleep_time=0)
    common_lib.check_if820_response(
        ezp_peripheral.CMD_SET_SLEEP_PARAMS, ez_rsp)

    # Enable Sleep via GPIO
    app_logger.app_log_info("Put device to sleep for 30 seconds.")
    pp_peripheral.gpio_to_output_low(pp_peripheral.GPIO_16)
    pp_peripheral.gpio_to_output_low(pp_peripheral.GPIO_20)

    # Device will now sleep until awoken by the host.
    # This code can be commented out to keep the device sleeping.
    time.sleep(30)
    app_logger.app_log_info("Wake the device.")
    pp_peripheral.gpio_to_output_high(pp_peripheral.GPIO_20)
    pp_peripheral.gpio_to_output_high(pp_peripheral.GPIO_16)

    # Close the open com ports
    pp_peripheral.close()
    ezp_peripheral.close()
