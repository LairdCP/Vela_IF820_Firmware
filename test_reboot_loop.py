import logging
import time
import ezserial_host_api.ezslib as ez_serial
import common.ez_serial_port as ez_port

PORT_NAME = '/dev/cu.usbmodem34304'
# Binary mode is unstable now, use text mode
API_FORMAT = ez_serial.Packet.EZS_API_FORMAT_TEXT

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s: %(message)s', level=logging.INFO)

    ez, port = ez_port.open(PORT_NAME, 115200)
    ez.defaults.apiformat = API_FORMAT
    ez.sendAndWait('protocol_set_parse_mode', rxtimeout=1, mode=API_FORMAT)

    while (True):
        try:
            logging.info('Send reboot')
            res = ez.sendAndWait('system_reboot', rxtimeout=1)
            logging.info('Wait for boot...')
            res = ez.waitEvent('system_boot')
            logging.info(f'Event: {res}')
        except Exception as e:
            logging.error(e)
            ez.reset()
            port.reset_input_buffer()
            ez_port.clear_rx_queue()
        time.sleep(5)
