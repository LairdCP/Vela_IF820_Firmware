#!/usr/bin/env python3

"""This sample configures a peripheral device to advertise the TX power the device is set to.
The actual TX power is set to match what is advertised.
To run this sample you need one IF820 DVK board.
"""

import argparse
import logging
import time
import sys
import ezserial_host_api.ezslib as ez_serial
import common.EzSerialPort as ez_port

API_FORMAT = ez_serial.Packet.EZS_API_FORMAT_TEXT
BOOT_DELAY_SECONDS = 3
ADV_MODE = ez_port.GapAdvertMode.NA.value
ADV_TYPE = ez_port.GapAdvertType.NON_CONNECTABLE_HIGH_DUTY_CYCLE.value
ADV_INTERVAL = 0x20
ADV_CHANNELS = ez_port.GapAdvertChannels.CHANNEL_ALL.value
ADV_TIMEOUT = 0
ADV_FLAGS = ez_port.GapAdvertFlags.ALL.value
ADV_DATA = [0x02, 0x01, 0x06,
            0x02, 0x0A, 0x00]
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true',
                        help="Enable verbose debug messages")
    parser.add_argument('-p', '--peripheral',
                        required=True, help="COM port for peripheral device")
    parser.add_argument('-t', '--tx_power', type=int, default=2,
                        help="TX power level index (1-8)")
    logging.basicConfig(format='%(asctime)s: %(message)s', level=logging.INFO)
    args, unknown = parser.parse_known_args()
    if args.debug:
        logging.info("Debugging mode enabled")
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.info("Debugging mode disabled")

    tx_power = args.tx_power
    peripheral = ez_port.EzSerialPort()
    peripheral.open(args.peripheral, peripheral.IF820_DEFAULT_BAUD)
    peripheral.set_api_format(API_FORMAT)

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

    res = peripheral.send_and_wait(peripheral.CMD_GET_TX_POWER)
    power_tables = res[1].payload.power_array
    logging.debug(f'TX power tables: {power_tables}')

    ble_tx_power_table = power_tables[-8:]
    logging.debug(f'BLE TX power table: {ble_tx_power_table}')

    # Set TX power
    quit_on_resp_err(peripheral.send_and_wait(peripheral.CMD_SET_TX_POWER,
                                              power=tx_power,
                                              power_array=[])[0])
    # Set TX power in advertisement data
    power = ble_tx_power_table[tx_power - 1]
    ADV_DATA[-1] = power
    quit_on_resp_err(peripheral.send_and_wait(peripheral.CMD_GAP_SET_ADV_DATA,
                                              data=ADV_DATA)[0])
    # Start advertising
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
    logging.info(f'Advertising at power level {power} dBm')
