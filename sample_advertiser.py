#!/usr/bin/env python3

"""The advertiser sample configures a peripheral device to advertise a custom
payload and a central device to scan for the peripheral device.
The custom advertisement payload contains a 1 byte counter value that is incremented
every two seconds.
The central device prints the counter value when it receives a new advertisement.
To run this test you need two IF820 DVK boards.
"""

import argparse
import logging
import time
import sys
import threading
import ezserial_host_api.ezslib as ez_serial
import common.EzSerialPort as ez_port

API_FORMAT = ez_serial.Packet.EZS_API_FORMAT_BINARY
BOOT_DELAY_SECONDS = 3
ADV_MODE = ez_port.GapAdvertMode.NA.value
ADV_TYPE = ez_port.GapAdvertType.NON_CONNECTABLE_LOW_DUTY_CYCLE.value
ADV_INTERVAL = 0x40
ADV_CHANNELS = ez_port.GapAdvertChannels.CHANNEL_ALL.value
ADV_TIMEOUT = 0
ADV_FLAGS = ez_port.GapAdvertFlags.ALL.value
ADV_DATA = [0x02, 0x01, 0x06, 0x0a, 0x08, 0x6d, 0x79, 0x5f, 0x73, 0x65, 0x6e,
            0x73, 0x6f, 0x72, 0x04, 0xff, 0x77, 0x00, 0x01]
SCAN_MODE_GENERAL_DISCOVERY = ez_port.GapScanMode.NA.value
SCAN_FILTER_ACCEPT_ALL = ez_port.GapScanFilter.NA.value
PERIPHERAL_ADDRESS = None


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
    quit_on_resp_err(dev.send_and_wait(dev.CMD_REBOOT)[0])
    res = dev.wait_event(dev.EVENT_SYSTEM_BOOT)
    quit_on_resp_err(res[0])
    time.sleep(BOOT_DELAY_SECONDS)
    return res[1]


def scanner_thread():
    """Thread to scan for the peripheral device and print the counter value.
    """
    last_counter = -1
    logging.info('Configure scanner...')
    res = reboot_the_device(central)
    logging.info(f'Scanner: {res}')
    quit_on_resp_err(central.send_and_wait(central.CMD_GAP_START_SCAN,
                                           mode=SCAN_MODE_GENERAL_DISCOVERY,
                                           interval=0x400,
                                           window=0x400,
                                           active=0,
                                           filter=SCAN_FILTER_ACCEPT_ALL,
                                           nodupe=0,
                                           timeout=0)[0])
    while True:
        res = central.wait_event(central.EVENT_GAP_SCAN_RESULT)
        quit_on_resp_err(res[0])
        packet = res[1]
        logging.debug(f'Received {packet}')
        received_addr = packet.payload.address
        if received_addr == PERIPHERAL_ADDRESS:
            counter = packet.payload.data[-1]
            if counter != last_counter:
                last_counter = counter
                logging.info(f'Received value {counter}')
            else:
                logging.debug('Received duplicate advert')
        else:
            logging.debug(f'Not looking for {received_addr}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--central',
                        required=True, help="COM port for central device")
    parser.add_argument('-d', '--debug', action='store_true',
                        help="Enable verbose debug messages")
    parser.add_argument('-p', '--peripheral',
                        required=True, help="COM port for peripheral device")
    logging.basicConfig(format='%(asctime)s: %(message)s', level=logging.INFO)
    args, unknown = parser.parse_known_args()
    if args.debug:
        logging.info("Debugging mode enabled")
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.info("Debugging mode disabled")

    central = ez_port.EzSerialPort()
    central.open(args.central, central.IF820_DEFAULT_BAUD)
    central.set_api_format(API_FORMAT)
    peripheral = ez_port.EzSerialPort()
    peripheral.open(args.peripheral, peripheral.IF820_DEFAULT_BAUD)
    peripheral.set_api_format(API_FORMAT)

    threading.Thread(target=scanner_thread,
                     daemon=True).start()

    logging.info('Configure advertiser...')
    res = reboot_the_device(peripheral)
    logging.info(f'Advertiser: {res}')
    PERIPHERAL_ADDRESS = res.payload.address
    quit_on_resp_err(peripheral.send_and_wait(peripheral.CMD_GAP_STOP_ADV)[0])
    quit_on_resp_err(peripheral.send_and_wait(peripheral.CMD_GAP_SET_ADV_PARAMETERS,
                                              mode=ADV_MODE,
                                              type=ADV_TYPE,
                                              channels=ADV_CHANNELS,
                                              high_interval=ADV_INTERVAL,
                                              high_duration=ADV_TIMEOUT,
                                              low_interval=ADV_INTERVAL,
                                              low_duration=ADV_TIMEOUT,
                                              flags=ADV_FLAGS,
                                              directAddr=[0, 0, 0, 0, 0, 0],
                                              directAddrType=ez_port.GapAddressType.PUBLIC.value)[0])
    quit_on_resp_err(peripheral.send_and_wait(peripheral.CMD_GAP_SET_ADV_DATA,
                                              data=ADV_DATA)[0])
    quit_on_resp_err(peripheral.send_and_wait(peripheral.CMD_GAP_START_ADV,
                                              mode=ADV_MODE,
                                              type=ADV_TYPE,
                                              channels=ADV_CHANNELS,
                                              high_interval=ADV_INTERVAL,
                                              high_duration=ADV_TIMEOUT,
                                              low_interval=ADV_INTERVAL,
                                              low_duration=ADV_TIMEOUT,
                                              flags=ADV_FLAGS,
                                              directAddr=[0, 0, 0, 0, 0, 0],
                                              directAddrType=ez_port.GapAddressType.PUBLIC.value)[0])

    while (True):
        time.sleep(2)
        counter = ADV_DATA[-1]
        counter = counter + 1
        if counter >= 256:
            counter = 0
        ADV_DATA[-1] = counter
        logging.info(f'Advertising value {counter}')
        quit_on_resp_err(peripheral.send_and_wait(peripheral.CMD_GAP_SET_ADV_DATA,
                                                  data=ADV_DATA)[0])
