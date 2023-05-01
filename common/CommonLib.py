import logging
import sys

OK = "OK"


class CommonLib:
    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'

    def check_bt900_response(self, response: str, expected_response: str = OK):
        # decode raw bytes from serial port to utf-84
        string_utf8 = bytes(response).decode('utf-8')
        if (expected_response in string_utf8):
            logging.info(f"BT900 response = {string_utf8}")
        else:
            sys.exit(f"BT900 response error! {string_utf8}")

    def check_if820_response(self, request: str, response):
        if response[0] == 0:
            logging.info(f'{request} Result: {response}')
        else:
            sys.exit(f'{request} Result: {response}')

    def if820_mac_addr_response_to_mac_as_string(self, response) -> str:
        response.reverse()
        str_mac = bytearray(response).hex()
        return str_mac
