#!/usr/bin/env python3

import argparse
import logging
import time
import common.EzSerialPort as ez_port
import common.SerialPort as serial_port
import common.PicoProbe as pico_probe
from common.BT900SerialPort import BT900SerialPort
from common.CommonLib import CommonLib
from common.AppLogging import AppLogging
from ezserial_host_api.ezslib import Packet

SCAN_MODE = ez_port.GapScanMode.NA.value
SCAN_INTERVAL = 0x40
SCAN_WINDOW = 0x40
SCAN_FILTER_ACCEPT_ALL = ez_port.GapScanFilter.NA.value
PERIPHERAL_ADDRESS = None
BT900_ADV_FLAGS = bytes([0x02, 0x01, 0x06])
BT900_ADV_NAME = bytes([0x0C, 0x09, 0x4C, 0x41, 0x49,
                       0x52, 0x44, 0x20, 0x42, 0x54, 0x39, 0x30, 0x30])

"""
Hardware Setup
This sample requires the following hardware:
-BT900 connected to PC via USB to act as a Bluetooth Peripheral.  SIO19 must be pulled to ground via jumper.
 *** The BT900 should be reset before the test to ensure it is advertising ***
-IF820 connected to PC via USB to act as a Bluetooth Central.
"""

CYSPP_DATA = "abcdefghijklmnop"

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-cp', '--connection_p',
                        required=True, help="Peripheral COM port")
    parser.add_argument('-cc', '--connection_c',
                        required=True, help="Central COM port")
    parser.add_argument('-ppc', '--picoprobe_c',
                        required=True, help="Pico Probe Id Central")
    parser.add_argument('-d', '--debug', action='store_true',
                        help="Enable verbose debug messages")
    logging.basicConfig(format='%(asctime)s: %(message)s', level=logging.INFO)
    args, unknown = parser.parse_known_args()
    if args.debug:
        app_logger = AppLogging("if820-bt900")
        app_logger.configure_app_logging(
            level=app_logger.DEBUG, file_level=app_logger.NOTSET)
        app_logger.app_log_info("Debugging mode enabled")

    common_lib = CommonLib()

    # open devices
    # bt900
    bt900_peripheral = BT900SerialPort()
    open_result = bt900_peripheral.device.open(
        args.connection_p, bt900_peripheral.BT900_DEFAULT_BAUD)
    if (not open_result):
        raise Exception(
            f"Error!  Unable to open bt900 peripheral at {args.connection_p}")

    # IF820
    if820_central = ez_port.EzSerialPort()
    open_result = if820_central.open(args.connection_c, 115200)
    if (not open_result):
        raise Exception(
            f"Error!  Unable to open if820 ez_central at {args.connection_c}")
    if820_central.set_queue_timeout(2)

    # Pico Probe attached to central
    pp_central = pico_probe.PicoProbe()
    pp_central.open(args.picoprobe_c)
    if (not pp_central.is_open):
        app_logger.app_log_critical("Unable to open Pico Probe.")

    # End CYSPP if active
    pp_central.gpio_to_output(pp_central.GPIO_19)
    pp_central.gpio_to_output_high(pp_central.GPIO_19)
    pp_central.gpio_to_input(pp_central.GPIO_19)

    # Put into central mode by setting CP_ROLE (GPIO18 low)
    pp_central.gpio_to_output(pp_central.GPIO_18)
    pp_central.gpio_to_output_low(pp_central.GPIO_18)

    # IF820 Ping
    ez_rsp = if820_central.send_and_wait(if820_central.CMD_PING)
    common_lib.check_if820_response(if820_central.CMD_PING, ez_rsp)

    # IF820 Factory Reset
    ez_rsp = if820_central.send_and_wait(if820_central.CMD_FACTORY_RESET)
    common_lib.check_if820_response(if820_central.CMD_FACTORY_RESET, ez_rsp)
    ez_rsp = if820_central.wait_event(if820_central.EVENT_SYSTEM_BOOT)
    common_lib.check_if820_response(if820_central.CMD_PING, ez_rsp)

    bt900_addr = None
    while (bt900_addr == None):
        ez_rsp = if820_central.wait_event(if820_central.EVENT_GAP_SCAN_RESULT)
        common_lib.check_if820_response(
            if820_central.EVENT_GAP_SCAN_RESULT, ez_rsp)
        packet = ez_rsp[1]
        if ((packet.payload.address_type == 0) and
            (packet.payload.data.startswith(BT900_ADV_FLAGS)) and
                (packet.payload.data.endswith(BT900_ADV_NAME))):
            bt900_addr = packet.payload.address
            address_type = packet.payload.address_type
            app_logger.app_log_info(bt900_addr)

    ez_rsp = if820_central.send_and_wait(if820_central.CMD_GAP_STOP_SCAN)
    common_lib.check_if820_response(if820_central.CMD_GAP_STOP_SCAN, ez_rsp)

    # IF820(central) connect to BT900 (peripheral)
    conn_handle = None
    response = if820_central.send_and_wait(command=if820_central.CMD_GAP_CONNECT,
                                           apiformat=Packet.EZS_API_FORMAT_TEXT,
                                           address=bt900_addr,
                                           type=0,
                                           interval=6,
                                           slave_latency=address_type,
                                           supervision_timeout=100,
                                           scan_interval=0x0100,
                                           scan_window=0x0100,
                                           scan_timeout=0)
    common_lib.check_if820_response(if820_central.CMD_GAP_CONNECT, response)
    ez_rsp = if820_central.wait_event(if820_central.EVENT_GAP_CONNECTED)
    conn_handle = ez_rsp[1].payload.conn_handle
    wait_for_rpc = False

    # wait for result events to pour in - we don't need them.
    time.sleep(6)

    # enable notifications on characteristic
    if820_central.clear_rx_queue()
    ez_rsp = if820_central.send_and_wait(command=if820_central.CMD_GATTC_WRITE_HANDLE,
                                         apiformat=Packet.EZS_API_FORMAT_TEXT,
                                         conn_handle=conn_handle,
                                         attr_handle=0x16,
                                         type=0,
                                         data=[0x01, 0x00])
    common_lib.check_if820_response(
        if820_central.CMD_GATTC_WRITE_HANDLE, ez_rsp)
    time.sleep(0.5)

    # Send data on CYSPP.
    ez_rsp = if820_central.send_and_wait(command=if820_central.CMD_GATTC_WRITE_HANDLE,
                                         apiformat=Packet.EZS_API_FORMAT_TEXT,
                                         conn_handle=conn_handle,
                                         attr_handle=0x13,
                                         type=1,
                                         data=[0x30, 0x31, 0x32, 0x33, 0x34, 0x35])
    common_lib.check_if820_response(
        if820_central.CMD_GATTC_WRITE_HANDLE, ez_rsp)

    time.sleep(0.5)
    rx_data = bt900_peripheral.device.get_rx_queue()
    string_utf8 = bytes(rx_data).decode('utf-8')
    app_logger.app_log_info(f"IF820->BT900 Data = {string_utf8}")

    # send data from BT900 -> IF820
    time.sleep(0.5)
    bt900_peripheral.device.send('a')
    ez_rsp = if820_central.wait_event(if820_central.EVENT_GATTC_DATA_RECEIVED)
    common_lib.check_if820_response(
        if820_central.EVENT_GATTC_DATA_RECEIVED, ez_rsp)
    rx_data = ez_rsp[1].payload.data
    string_utf8 = bytes(rx_data).decode('utf-8')
    app_logger.app_log_info(f"BT900->IF820 Data = {string_utf8}")

    # End CYSPP Mode on both devices, and close open connections.
    pp_central.gpio_to_output(pp_central.GPIO_19)
    pp_central.gpio_to_output_high(pp_central.GPIO_19)
    pp_central.gpio_to_input(pp_central.GPIO_19)
    pp_central.gpio_to_input(pp_central.GPIO_18)
    pp_central.close()
    bt900_peripheral.device.close()
    if820_central.close()
