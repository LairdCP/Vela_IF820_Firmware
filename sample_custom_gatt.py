#!/usr/bin/env python3

"""The custom GATT sample configures a peripheral device to advertise a custom
payload and sets up the BT SIG GATT Battery Service (https://www.bluetooth.com/specifications/specs/battery-service/). Every 5 seconds, the peripheral will
change the battery level.
A central device scans for the peripheral device and connects to it.
The central device will received the battery level every time it is updated.
To run this test you need two IF820 DVK boards.
"""

import argparse
import logging
import time
import sys
import threading
import ezserial_host_api.ezslib as ez_serial
import common.EzSerialPort as ez_port
from common.If820Board import If820Board

API_FORMAT = ez_serial.Packet.EZS_API_FORMAT_BINARY
BOOT_DELAY_SECONDS = 3
ADV_MODE = ez_port.GapAdvertMode.NA.value
ADV_TYPE = ez_port.GapAdvertType.UNDIRECTED_LOW_DUTY_CYCLE.value
ADV_INTERVAL = 0x40
ADV_CHANNELS = ez_port.GapAdvertChannels.CHANNEL_ALL.value
ADV_TIMEOUT = 0
ADV_FLAGS = ez_port.GapAdvertFlags.ALL.value
ADV_DATA = [0x02, 0x01, 0x06,
            0x08, 0x08, 0x62, 0x61, 0x74, 0x74, 0x65, 0x72, 0x79,
            0x03, 0x02, 0x0f, 0x18]
SCAN_MODE_GENERAL_DISCOVERY = ez_port.GapScanMode.NA.value
SCAN_FILTER_ACCEPT_ALL = ez_port.GapScanFilter.NA.value
PERIPHERAL_ADDRESS = None
battery_level = 100
battery_level_handle = 0
batter_level_ccc_handle = 0


def quit_on_resp_err(resp: int):
    """Exit the program if the response code is not 0.

    Args:
        resp (int): response code
    """
    if resp != 0:
        sys.exit(f'Response err: {hex(resp)}')


def reboot_the_device(dev: ez_port.EzSerialPort) -> object:
    """Reboot the device

    Args:
        dev (ez_port.EzSerialPort): The device to reboot

    Returns:
        object: The packet object from the reboot event
    """
    quit_on_resp_err(dev.send_and_wait(
        dev.CMD_REBOOT)[0])
    res = dev.wait_event(dev.EVENT_SYSTEM_BOOT)
    quit_on_resp_err(res[0])
    time.sleep(BOOT_DELAY_SECONDS)
    return res[1]


def scanner_thread():
    """Thread to scan for the peripheral device and connect to it.
    """
    logging.info('Configure scanner...')
    res = reboot_the_device(if820_board_c.p_uart)
    logging.info(f'Scanner: {res}')
    quit_on_resp_err(if820_board_c.p_uart.send_and_wait(if820_board_c.p_uart.CMD_GAP_START_SCAN,
                                                        mode=SCAN_MODE_GENERAL_DISCOVERY,
                                                        interval=0x400,
                                                        window=0x400,
                                                        active=0,
                                                        filter=SCAN_FILTER_ACCEPT_ALL,
                                                        nodupe=1,
                                                        timeout=30)[0])
    while True:
        res = if820_board_c.p_uart.wait_event(
            if820_board_c.p_uart.EVENT_GAP_SCAN_RESULT)
        quit_on_resp_err(res[0])
        packet = res[1]
        logging.debug(f'Received {packet}')
        received_addr = packet.payload.address
        address_type = packet.payload.address_type
        if received_addr == PERIPHERAL_ADDRESS:
            break
        else:
            logging.debug(f'Not looking for {received_addr}')

    quit_on_resp_err(if820_board_c.p_uart.send_and_wait(
        if820_board_c.p_uart.CMD_GAP_STOP_SCAN)[0])

    quit_on_resp_err(if820_board_c.p_uart.send_and_wait(if820_board_c.p_uart.CMD_GAP_CONNECT,
                                                        address=received_addr,
                                                        type=address_type,
                                                        interval=6,
                                                        slave_latency=0,
                                                        supervision_timeout=100,
                                                        scan_interval=0x0100,
                                                        scan_window=0x0100,
                                                        scan_timeout=0)[0])

    logging.info('Found peripheral device, connecting...')
    res = if820_board_c.p_uart.wait_event(
        if820_board_c.p_uart.EVENT_GAP_CONNECTED)
    quit_on_resp_err(res[0])
    logging.info('Connected!')

    # Enable notifications for battery level
    res = if820_board_c.p_uart.send_and_wait(if820_board_c.p_uart.CMD_GATTC_WRITE_HANDLE,
                                             conn_handle=0,
                                             attr_handle=batter_level_ccc_handle,
                                             type=0,
                                             data=[0x01, 0x00])

    while True:
        try:
            res = if820_board_c.p_uart.wait_event(
                if820_board_c.p_uart.EVENT_GATTC_DATA_RECEIVED)
            if res[0] == 0 and res[1].payload.attr_handle == battery_level_handle:
                logging.info(
                    f'Received battery level {res[1].payload.data[0]}')
            else:
                logging.error(f'Error receiving data: {hex(res[0])}')
        except:
            pass


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

    boards = If820Board.get_connected_boards()
    if len(boards) < 2:
        logging.critical(
            "Two IF820 boards required for this sample.")
        exit(1)

    if820_board_p = boards[0]
    if820_board_c = boards[1]

    if820_board_p = boards[0]
    if820_board_c = boards[1]
    if820_board_p.open_and_init_board()
    if820_board_c.open_and_init_board()
    if820_board_c.p_uart.set_api_format(API_FORMAT)
    if820_board_p.p_uart.set_api_format(API_FORMAT)

    logging.info('Configure advertiser...')
    res = reboot_the_device(if820_board_p.p_uart)
    logging.info(f'Advertiser: {res}')
    PERIPHERAL_ADDRESS = res.payload.address
    quit_on_resp_err(if820_board_p.p_uart.send_and_wait(
        if820_board_p.p_uart.CMD_GAP_STOP_ADV)[0])

    # Start scanner thread
    threading.Thread(target=scanner_thread,
                     daemon=True).start()

    # Set advertising parameters
    quit_on_resp_err(if820_board_p.p_uart.send_and_wait(if820_board_p.p_uart.CMD_GAP_SET_ADV_PARAMETERS,
                                                        mode=ADV_MODE,
                                                        type=ADV_TYPE,
                                                        channels=ADV_CHANNELS,
                                                        high_interval=ADV_INTERVAL,
                                                        high_duration=ADV_TIMEOUT,
                                                        low_interval=ADV_INTERVAL,
                                                        low_duration=ADV_TIMEOUT,
                                                        flags=ADV_FLAGS,
                                                        directAddr=[
                                                            0, 0, 0, 0, 0, 0],
                                                        directAddrType=ez_port.GapAddressType.PUBLIC.value)[0])
    # Set custom advertising data
    quit_on_resp_err(if820_board_p.p_uart.send_and_wait(if820_board_p.p_uart.CMD_GAP_SET_ADV_DATA,
                                                        data=ADV_DATA)[0])

    # Setup Battery Service
    # Create battery service descriptor
    quit_on_resp_err(if820_board_p.p_uart.send_and_wait(
        if820_board_p.p_uart.CMD_GATTS_CREATE_ATTR,
        type=ez_port.GattAttrType.STRUCTURE.value,
        perm=ez_port.GattAttrPermission.READ.value,
        length=4,
        data=bytearray.fromhex('00280F18'))[0])
    # Create battery level characteristic descriptor
    quit_on_resp_err(if820_board_p.p_uart.send_and_wait(
        if820_board_p.p_uart.CMD_GATTS_CREATE_ATTR,
        type=ez_port.GattAttrType.STRUCTURE.value,
        perm=ez_port.GattAttrPermission.READ.value,
        length=7,
        data=bytearray.fromhex('0328121800192A'))[0])
    # Create battery level characteristic value descriptor
    res = if820_board_p.p_uart.send_and_wait(
        if820_board_p.p_uart.CMD_GATTS_CREATE_ATTR,
        type=ez_port.GattAttrType.VALUE.value,
        perm=ez_port.GattAttrPermission.READ.value | ez_port.GattAttrPermission.AUTH_WRITE.value,
        length=1,
        data=[battery_level])
    quit_on_resp_err(res[0])
    battery_level_handle = res[1].payload.handle
    # Create battery level Client Characteristic Configuration descriptor
    res = if820_board_p.p_uart.send_and_wait(
        if820_board_p.p_uart.CMD_GATTS_CREATE_ATTR,
        type=ez_port.GattAttrType.STRUCTURE.value,
        perm=ez_port.GattAttrPermission.READ.value | ez_port.GattAttrPermission.WRITE_ACK.value,
        length=4,
        data=bytearray.fromhex('02290000'))
    quit_on_resp_err(res[0])
    batter_level_ccc_handle = res[1].payload.handle

    # Start advertising
    quit_on_resp_err(if820_board_p.p_uart.send_and_wait(if820_board_p.p_uart.CMD_GAP_START_ADV,
                                                        mode=ADV_MODE,
                                                        type=ADV_TYPE,
                                                        channels=ADV_CHANNELS,
                                                        high_interval=ADV_INTERVAL,
                                                        high_duration=0,
                                                        low_interval=ADV_INTERVAL,
                                                        low_duration=0,
                                                        flags=ADV_FLAGS,
                                                        directAddr=[
                                                            0, 0, 0, 0, 0, 0],
                                                        directAddrType=ez_port.GapAddressType.PUBLIC.value)[0])

    while (True):
        time.sleep(5)
        battery_level -= 1
        if battery_level < 0:
            battery_level = 100

        try:
            res = if820_board_p.p_uart.send_and_wait(if820_board_p.p_uart.CMD_GATTS_WRITE_HANDLE,
                                                     attr_handle=battery_level_handle,
                                                     data=[battery_level])
            if res[0] == 0:
                logging.info(f'Changed battery level: {battery_level}')
            else:
                logging.error(
                    f'Failed to change battery level {battery_level} [{hex(res[0])}]')
                continue

            # Notify that battery level has changed to any connected device subscribed to notifications
            res = if820_board_p.p_uart.send_and_wait(if820_board_p.p_uart.CMD_GATTS_NOTIFY_HANDLE,
                                                     conn_handle=0,
                                                     attr_handle=battery_level_handle,
                                                     data=[battery_level])
            if res[0] != 0:
                logging.error(
                    f'Failed to notify battery level {battery_level} [{hex(res[0])}]')
        except:
            pass
