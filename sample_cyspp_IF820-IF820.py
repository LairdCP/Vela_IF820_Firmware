#!/usr/bin/env python3

import argparse
import time
import sys
import common.EzSerialPort as ez_port
import common.SerialPort as serial_port
import common.PicoProbe as pico_probe
from common.CommonLib import CommonLib
from common.AppLogging import AppLogging

"""
Hardware Setup
This sample requires the following hardware:
-IF820 connected to PC via USB to act as a Bluetooth Peripheral
-IF820 connected to PC via USB to act as a Bluetooth Central
-P27 is the "Connection" indicator.  On the Laird Module this is pin 33 of the module, attached to GPIO8 of the pico probe.
"""

FLAG_INQUIRY_NAME = 1
CY_SPP_DATA = "abcdefghijklmnop"

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-cp', '--connection_p',
                        required=True, help="Peripheral COM port")
    parser.add_argument('-cc', '--connection_c',
                        required=True, help="Central COM port")
    parser.add_argument('-ppp', '--picoprobe_p',
                        required=True, help="Pico Probe Id Perhipheral")
    parser.add_argument('-ppc', '--picoprobe_c',
                        required=True, help="Pico Probe Id Central")
    parser.add_argument('-d', '--debug', action='store_true',
                        help="Enable verbose debug messages")
    args, unknown = parser.parse_known_args()
    app_logger = AppLogging("cyspp if820-if820")
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

    ezp_central = ez_port.EzSerialPort()
    open_result = ezp_central.open(
        args.connection_c, ezp_central.IF820_DEFAULT_BAUD)
    if (not open_result[1]):
        raise Exception(
            f"Error!  Unable to open ez_peripheral at {args.connection_c}")

    pp_peripheral = pico_probe.PicoProbe()
    pp_central = pico_probe.PicoProbe()
    pp_peripheral.open(args.picoprobe_p)
    if (not pp_peripheral.is_open):
        app_logger.app_log_critical("Unable to open Pico Probe.")
    pp_central.open(args.picoprobe_c)
    if (not pp_central.is_open):
        app_logger.app_log_critical("Unable to open Pico Probe.")

    # ensure SPP enable on module by setting pico gpio to input
    pp_peripheral.gpio_to_input(pp_peripheral.GPIO_19)
    pp_central.gpio_to_input(pp_peripheral.GPIO_19)

    # Send Ping just to verify coms before proceeding
    ez_rsp = ezp_peripheral.send_and_wait(ezp_peripheral.CMD_PING)
    common_lib.check_if820_response(ezp_peripheral.CMD_PING, ez_rsp)
    ez_rsp = ezp_central.send_and_wait(ezp_central.CMD_PING)
    common_lib.check_if820_response(ezp_central.CMD_PING, ez_rsp)

    # Factory Reset Peripheral
    ezp_peripheral.send_and_wait(ezp_peripheral.CMD_FACTORY_RESET)
    common_lib.check_if820_response(ezp_peripheral.CMD_FACTORY_RESET, ez_rsp)
    ez_rsp = ezp_peripheral.wait_event(ezp_peripheral.EVENT_SYSTEM_BOOT)
    common_lib.check_if820_response(ezp_peripheral.EVENT_SYSTEM_BOOT, ez_rsp)

    # Factory Reset Central
    ezp_central.send_and_wait(ezp_central.CMD_FACTORY_RESET)
    common_lib.check_if820_response(ezp_central.CMD_FACTORY_RESET, ez_rsp)
    ez_rsp = ezp_central.wait_event(ezp_central.EVENT_SYSTEM_BOOT)
    common_lib.check_if820_response(ezp_central.EVENT_SYSTEM_BOOT, ez_rsp)

    # Set Central CY_ROLE pin low to boot in central mode
    pp_central.gpio_to_output(pp_central.GPIO_18)
    pp_central.gpio_to_output_low(pp_central.GPIO_18)
    """
    Todo:  get device into central mode using api.  See Jira Issue L2-140.
    Right now the central role is obtained by changing GPIO_18 above.
    ezp_central.send(ezp_central.CMD_P_CYSPP_SET_PARAMETERS,
                     enable=2,
                     role=1,
                     company=305,
                     local_key=0,
                     remote_key=0,
                     remote_mask=0,
                     sleep_level=0,
                     server_security=0,
                     client_flags=2)
    """
    # Reboot the Central
    ezp_central.send_and_wait(ezp_central.CMD_REBOOT)

    wait_for_conn = True
    while (wait_for_conn):
        ez_rsp = ezp_central.wait_event(ezp_central.EVENT_P_CYSPP_STATUS)
        app_logger.app_log_info(ez_rsp)
        if ez_rsp[1].payload.status == 53:
            wait_for_conn = False

    # close ez serial ports
    ezp_peripheral.close()
    ezp_central.close()

    # open serial ports
    sp_peripheral = serial_port.SerialPort()
    sp_central = serial_port.SerialPort()
    sp_peripheral.open(args.connection_p, 115200)
    sp_central.open(args.connection_c, 115200)

    # send data from central to peripheral
    for c in CY_SPP_DATA:
        sp_central.send(c)
        time.sleep(0.02)
    # wait 1 sec to ensure all data is sent and received
    time.sleep(1)
    rx_data = sp_peripheral.get_rx_queue()
    string_utf8 = bytes(rx_data).decode('utf-8')
    app_logger.app_log_debug(
        f"Received SPP Data Central->Peripheral: {string_utf8}")
    if (len(string_utf8) == 0):
        sys.exit(f"Error!  No data recived over SPP.")

     # send data from peripheral to central
    for c in CY_SPP_DATA:
        sp_peripheral.send(c)
        time.sleep(0.02)
    # wait 1 sec to ensure all data is sent and received
    time.sleep(1)
    rx_data = sp_central.get_rx_queue()
    string_utf8 = bytes(rx_data).decode('utf-8')
    app_logger.app_log_debug(
        f"Received SPP Data Peripheral->Central: {string_utf8}")
    if (len(string_utf8) == 0):
        sys.exit(f"Error!  No data recived over SPP.")

     # clean everything up
    # disable spp mode by changing state of P13 of IF820
    pp_peripheral.gpio_to_output(pp_peripheral.GPIO_19)
    pp_peripheral.gpio_to_output_high(pp_peripheral.GPIO_19)
    pp_peripheral.gpio_to_input(pp_peripheral.GPIO_19)
    pp_peripheral.gpio_to_input(pp_peripheral.GPIO_18)
    pp_peripheral.close()
    pp_central.gpio_to_output(pp_central.GPIO_19)
    pp_central.gpio_to_output_high(pp_central.GPIO_19)
    pp_central.gpio_to_input(pp_central.GPIO_19)
    pp_central.gpio_to_input(pp_central.GPIO_18)
    pp_central.close()
    # close the open com ports
    sp_peripheral.close()
    sp_central.close()
