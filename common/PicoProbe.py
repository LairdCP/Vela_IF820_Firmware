import logging
import time
from pyocd.probe.pydapaccess import DAPAccessCMSISDAP

SET_IO_DIR_CMD = 31
SET_IO_CMD = 30
READ_IO_CMD = 29
HIGH = OUTPUT = 1
LOW = INPUT = 0


class PicoProbe:
    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'

    GPIO_00 = 0
    GPIO_01 = 1
    GPIO_02 = 2
    GPIO_03 = 3
    GPIO_04 = 4
    GPIO_05 = 5
    GPIO_06 = 6
    GPIO_07 = 7
    GPIO_08 = 8
    GPIO_09 = 9
    GPIO_10 = 10
    GPIO_11 = 11
    GPIO_12 = 12
    GPIO_13 = 13
    GPIO_14 = 14
    GPIO_15 = 15
    GPIO_16 = 16
    GPIO_17 = 17
    GPIO_18 = 18
    GPIO_19 = 19
    GPIO_20 = 20
    GPIO_21 = 21
    GPIO_22 = 22
    GPIO_26 = 26
    GPIO_27 = 27
    GPIO_28 = 28

    def __init__(self):
        for self.probe in DAPAccessCMSISDAP.get_connected_devices():
            logging.debug(f'Found probe: {self.probe.vendor_name}')

    def open(self, device_id: str):
        self.probe = DAPAccessCMSISDAP(device_id)
        self.probe.open()

    def is_open(self):
        return self.probe.is_open

    def close(self):
        self.probe.close()

    def gpio_read(self, gpio: int):
        res = self.probe.vendor(READ_IO_CMD, [gpio])
        return res[0]

    def gpio_to_input(self,  gpio: int):
        res = self.probe.vendor(SET_IO_DIR_CMD, [gpio, INPUT])

    def gpio_to_output(self,  gpio: int):
        res = self.probe.vendor(SET_IO_DIR_CMD, [gpio, OUTPUT])

    def gpio_to_output_low(self,  gpio: int):
        res = self.probe.vendor(SET_IO_CMD, [gpio, LOW])

    def gpio_to_output_high(self,  gpio: int):
        res = self.probe.vendor(SET_IO_CMD, [gpio, HIGH])

    def get_dap_info(self, id: int):
        result = self.probe.identify(DAPAccessCMSISDAP.ID(id))
        return result

    def get_dap_info1(self, id: DAPAccessCMSISDAP.ID):
        result = self.probe.identify(id)
        return result

    def get_dap_ids(self):
        return DAPAccessCMSISDAP.ID

    def reset_device(self):
        self.probe.assert_reset(True)
        time.sleep(0.050)
        self.probe.assert_reset(False)
        time.sleep(0.050)
