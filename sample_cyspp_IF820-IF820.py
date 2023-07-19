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

"""
Hardware Setup
This sample requires the following hardware:
-IF820 connected to PC via USB to act as a Bluetooth Peripheral
-IF820 connected to PC via USB to act as a Bluetooth Central
-P27 is the "Connection" indicator.  On the Laird Module this is pin 33 of the module, attached to GPIO8 of the pico probe.
"""
SCAN_MODE_GENERAL_DISCOVERY = ez_port.GapScanMode.NA.value
SCAN_FILTER_ACCEPT_ALL = ez_port.GapScanFilter.NA.value
FLAG_INQUIRY_NAME = 1
CY_SPP_DATA = "abcdefghijklmnop"
CENTRAL_ROLE = 1
"""
There are two ways to set a device as a central.
Method 1:  GPIO
Method 2:  API Command
If using the API command method, additional api commands are required to connect to a device.
"""
GPIO_MODE = False

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

    # reset the module (if it was in cyspp before it can't accept commands)
    pp_peripheral.gpio_to_output(pp_peripheral.GPIO_13)
    pp_central.gpio_to_output(pp_central.GPIO_13)
    pp_peripheral.gpio_to_output_low(pp_peripheral.GPIO_13)
    pp_central.gpio_to_output_low(pp_central.GPIO_13)
    time.sleep(0.05)
    pp_peripheral.gpio_to_output_high(pp_peripheral.GPIO_13)
    pp_central.gpio_to_output_high(pp_central.GPIO_13)
    pp_peripheral.gpio_to_input(pp_peripheral.GPIO_13)
    pp_central.gpio_to_input(pp_central.GPIO_13)

    # ensure SPP enable on module by setting pico gpio to input
    pp_peripheral.gpio_to_input(pp_peripheral.GPIO_19)
    pp_central.gpio_to_input(pp_peripheral.GPIO_19)

    # ensure CY_ROLE is not asserted
    pp_central.gpio_to_input(pp_peripheral.GPIO_18)

    # give the module time to finish boot
    time.sleep(0.5)

    # Send Ping just to verify coms before proceeding
    ez_rsp = ezp_peripheral.send_and_wait(ezp_peripheral.CMD_PING)
    common_lib.check_if820_response(ezp_peripheral.CMD_PING, ez_rsp)
    ez_rsp = ezp_central.send_and_wait(ezp_central.CMD_PING)
    common_lib.check_if820_response(ezp_central.CMD_PING, ez_rsp)

    # Factory Reset Peripheral
    ez_rsp = ezp_peripheral.send_and_wait(ezp_peripheral.CMD_FACTORY_RESET)
    common_lib.check_if820_response(ezp_peripheral.CMD_FACTORY_RESET, ez_rsp)
    ez_rsp = ezp_peripheral.wait_event(ezp_peripheral.EVENT_SYSTEM_BOOT)
    common_lib.check_if820_response(ezp_peripheral.EVENT_SYSTEM_BOOT, ez_rsp)

    # Factory Reset Central
    ez_rsp = ezp_central.send_and_wait(ezp_central.CMD_FACTORY_RESET)
    common_lib.check_if820_response(ezp_central.CMD_FACTORY_RESET, ez_rsp)
    ez_rsp = ezp_central.wait_event(ezp_central.EVENT_SYSTEM_BOOT)
    common_lib.check_if820_response(ezp_central.EVENT_SYSTEM_BOOT, ez_rsp)

    # if820 get mac address of peripheral
    ez_rsp = ezp_peripheral.send_and_wait(
        command=ezp_peripheral.CMD_GET_BT_ADDR)
    common_lib.check_if820_response(ezp_peripheral.CMD_GET_BT_ADDR, ez_rsp)
    peripheral_addr = ez_rsp[1].payload.address
    app_logger.app_log_info(ez_rsp[1].payload.address)

    if GPIO_MODE:
        # Set Central CY_ROLE pin low to boot in central mode
        pp_central.gpio_to_output(pp_central.GPIO_18)
        pp_central.gpio_to_output_low(pp_central.GPIO_18)
        ezp_central.send_and_wait(ezp_central.CMD_REBOOT)

        wait_for_conn = True
        while (wait_for_conn):
            ez_rsp = ezp_central.wait_event(ezp_central.EVENT_P_CYSPP_STATUS)
            app_logger.app_log_info(ez_rsp)
            if ez_rsp[1].payload.status == 53:
                wait_for_conn = False

    else:
        # Get device into central mode using api.
        ez_rsp = ezp_central.send_and_wait(command=ezp_central.CMD_P_CYSPP_SET_PARAMETERS,
                                           apiformat=Packet.EZS_API_FORMAT_TEXT,
                                           enable=2,
                                           role=CENTRAL_ROLE,
                                           company=305,
                                           local_key=0,
                                           remote_key=0,
                                           remote_mask=0,
                                           sleep_level=0,
                                           server_security=0,
                                           client_flags=2)
        common_lib.check_if820_response(
            ezp_central.CMD_P_CYSPP_SET_PARAMETERS, ez_rsp)

        ez_rsp = ezp_central.send_and_wait(ezp_central.CMD_GAP_START_SCAN,
                                           mode=SCAN_MODE_GENERAL_DISCOVERY,
                                           interval=0x400,
                                           window=0x400,
                                           active=0,
                                           filter=SCAN_FILTER_ACCEPT_ALL,
                                           nodupe=1,
                                           timeout=5)
        common_lib.check_if820_response(
            ezp_central.CMD_GAP_START_SCAN, ez_rsp)

        while True:
            ez_rsp = ezp_central.wait_event(ezp_central.EVENT_GAP_SCAN_RESULT)
            common_lib.check_if820_response(
                ezp_central.EVENT_GAP_SCAN_RESULT, ez_rsp)
            packet = ez_rsp[1]
            app_logger.app_log_debug(f'Received {packet}')
            received_addr = packet.payload.address
            address_type = packet.payload.address_type
            if received_addr == peripheral_addr:
                break
            else:
                app_logger.app_log_debug(f'Not looking for {received_addr}')

        ez_rsp = ezp_central.send_and_wait(ezp_central.CMD_GAP_STOP_SCAN)
        common_lib.check_if820_response(
            ezp_central.CMD_GAP_STOP_SCAN, ez_rsp)

        ez_rsp = ezp_central.send_and_wait(ezp_central.CMD_GAP_CONNECT,
                                           address=received_addr,
                                           type=address_type,
                                           interval=6,
                                           slave_latency=0,
                                           supervision_timeout=100,
                                           scan_interval=0x0100,
                                           scan_window=0x0100,
                                           scan_timeout=0)
        common_lib.check_if820_response(
            ezp_central.CMD_GAP_CONNECT, ez_rsp)

        app_logger.app_log_info('Found peripheral device, connecting...')
        res = ezp_central.wait_event(ezp_central.EVENT_GAP_CONNECTED)
        common_lib.check_if820_response(
            ezp_central.EVENT_GAP_CONNECTED, ez_rsp)
        ezp_central.app_log_info('Connected!')
        # time for cyspp to be setup
        time.sleep(2)

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
        sys.exit(f"Error!  No data received over SPP.")

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
