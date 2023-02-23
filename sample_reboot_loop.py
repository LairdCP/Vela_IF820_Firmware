import argparse
import logging
import time
import sys
import ezserial_host_api.ezslib as ez_serial
import common.EzSerialPort as ez_port

# Binary mode is unstable now, use text mode
API_FORMAT = ez_serial.Packet.EZS_API_FORMAT_TEXT


def log_resp_err(resp: int):
    if resp != 0:
        logging.error(f'Response err: {resp}')


def quit_on_resp_err(resp: int):
    if resp != 0:
        sys.exit(f'Response err: {resp}')


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

    ezp = ez_port.EzSerialPort()
    ez, port = ezp.open(args.connection, 115200)
    ez.defaults.apiformat = API_FORMAT
    res = ezp.send_and_wait(command='protocol_set_parse_mode',
                            rxtimeout=1, mode=API_FORMAT)
    quit_on_resp_err(res)

    while (True):
        try:
            logging.info('Send reboot')
            log_resp_err(ezp.send_and_wait('system_reboot', rxtimeout=1))
            logging.info('Wait for boot...')
            res = ez.waitEvent('system_boot')
            logging.info(f'Event: {res}')
        except Exception as e:
            logging.error(e)
            ez.reset()
            port.reset_input_buffer()
            ezp.clear_rx_queue()
        time.sleep(5)
