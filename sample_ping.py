import argparse
import logging
import common.EzSerialPort as ez_port

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
    ezp.open(args.connection, 115200)
    res = ezp.send_and_wait('system_ping')
    if res == 0:
        logging.info(f'Ping result: {res}')
    else:
        logging.error(f'Response err: {res}')
