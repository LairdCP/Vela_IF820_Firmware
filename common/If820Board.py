import logging
from common.DvkProbe import DvkProbe
from common.HciSerialPort import HciSerialPort
from common.HciProgrammer import HciProgrammer
from common.EzSerialPort import EzSerialPort
from common.CommonLib import CommonLib

ERR_OK = 0
ERR_BOARD_NOT_FOUND = -1


class If820Board(DvkProbe):

    BT_DEV_WAKE = DvkProbe.GPIO_16
    BT_HOST_WAKE = DvkProbe.GPIO_17
    CP_ROLE = DvkProbe.GPIO_18
    CYSPP = DvkProbe.GPIO_19
    LP_MODE = DvkProbe.GPIO_20
    CONNECTION = DvkProbe.GPIO_21

    @staticmethod
    def get_board():
        """Helper method to get a single board, or prompt user to select a board
        in the case of multiples.

        Returns:
        Board to connect to.
        """
        board = None
        boards = If820Board.get_connected_boards()
        if len(boards) == 0:
            raise Exception(
                f"Error!  No Boards found.")

        choice = 0
        if len(boards) > 1:
            print("Which board do you want to use?")
            for i, board in enumerate(boards):
                print(f"{i}: {board.probe.id}")
            choice = int(input("Enter the number of the board: "))
        if choice > (len(boards) - 1):
            raise Exception(
                f"Error!  Invalid Board Number.")

        return boards[choice]

    @staticmethod
    def get_connected_boards() -> list['If820Board']:
        """Get a list of all connected boards.

        Returns:
            List: List of IF820 boards
        """
        boards = []
        for probe in DvkProbe.get_connected_probes():
            board = If820Board()
            board.probe = probe
            if not probe.ports[0].location:
                logging.warning(
                    f'No COM port location found for board {probe.id}, assuming HCI port {probe.ports[0].device}')

            board.hci_port_name = probe.ports[0].device
            board.puart_port_name = probe.ports[1].device
            boards.append(board)
        return boards

    @staticmethod
    def get_board_by_com_port(com_port: str):
        """Get a board that uses the specified COM port.

        Returns:
            If820Board: IF820 board or None if not found
        """
        for board in If820Board.get_connected_boards():
            if board.hci_port_name == com_port or board.puart_port_name == com_port:
                return board
        return None

    def open_and_init_board(self):
        """
        Opens the IF820 PUART at the default baud rate,
        opens the DvkProbe, and resets the IF280 Module.

        The PUART can then be accessed via instance.p_uart.
        The DvkProbe can then be accessed via instance.probe.
        """
        common_lib = CommonLib()
        # open ez-serial port
        self.p_uart = EzSerialPort()
        logging.info(f'Port Name: {self.puart_port_name}')
        open_result = self.p_uart.open(
            self.puart_port_name, self.p_uart.IF820_DEFAULT_BAUD)
        if (not open_result[1]):
            raise Exception(
                f"Error!  Unable to open device at {self.puart_port_name}")

        # open dvk probe
        logging.info(f"Opening Dvk Probe ID {self.probe.id}")
        self.probe.open(self.probe.id)
        if (not self.probe.is_open):
            raise Exception(
                f"Unable to open Dvk Probe at {self.probe.id}")

        # reset dvk and module
        self.probe.reset_device()
        ez_rsp = self.p_uart.wait_event(self.p_uart.EVENT_SYSTEM_BOOT)
        common_lib.check_if820_response(self.p_uart.EVENT_SYSTEM_BOOT, ez_rsp)

    def close_ports_and_reset(self):
        """
        Close all puart and reset the probe and module
        Note:  Resetting the probe resets the IO and the module.
        """
        if self.p_uart:
            self.p_uart.close()
        if self.probe:
            self.probe.reboot()
            self.probe.close()
        if self.hci_uart:
            self.hci_uart.close()

    def __init__(self):
        self._probe = super().__init__()
        self._hci_port_name = ""
        self._puart_port_name = ""
        self._hci_uart = ""
        self._p_uart = ""

    @property
    def probe(self):
        """Pico Probe / Dvk Probe"""
        return self._probe

    @probe.setter
    def probe(self, p: DvkProbe):
        self._probe = p

    @property
    def hci_port_name(self):
        """HCI UART Port Name (i.e. COM10)"""
        return self._hci_port_name

    @hci_port_name.setter
    def hci_port_name(self, p: str):
        self._hci_port_name = p

    @property
    def puart_port_name(self):
        """PUART Port Name (i.e. COM10)"""
        return self._puart_port_name

    @puart_port_name.setter
    def puart_port_name(self, p: str):
        self._puart_port_name = p

    @property
    def hci_uart(self):
        """HCI UART Port Instance"""
        return self._hci_uart

    @hci_uart.setter
    def hci_uart(self, u: HciSerialPort):
        self._hci_uart = u

    @property
    def p_uart(self):
        """PUART Port Instance"""
        return self._p_uart

    @p_uart.setter
    def p_uart(self, u: EzSerialPort):
        self._p_uart = u

    def enter_hci_download_mode(self, port: str = str()) -> int:
        """Put the board into HCI download mode.

        Parameters:
            port (str): Optional: HCI COM port. If not specified (None) and there is more than one
            board is connected, the user will be prompted to select a board.

        Returns:
            int: 0 if successful, negative error code if not successful
        """
        board = self
        if port:
            board_found = self.get_board_by_com_port(port)
            if board_found:
                board = board_found
            else:
                logging.error(f"Board not found with port {port}")
                return ERR_BOARD_NOT_FOUND

        self.hci_uart = HciSerialPort()
        logging.debug(f"Opening HCI port {board.hci_port_name}")
        self.hci_uart.open(board.hci_port_name,
                           HciProgrammer.HCI_DEFAULT_BAUDRATE)
        board.probe.open()
        board.probe.reset_device()
        board.probe.close()
        self.hci_uart.close()
        return ERR_OK

    def flash_firmware(self, minidriver: str, firmware: str, chip_erase: bool = False) -> int:
        res = self.enter_hci_download_mode()
        if res != ERR_OK:
            raise Exception("Failed to enter HCI download mode")

        self.hci_programmer = HciProgrammer(minidriver, self.hci_port_name,
                                            HciProgrammer.HCI_DEFAULT_BAUDRATE, chip_erase)
        self.hci_programmer.program_firmware(
            HciProgrammer.HCI_FLASH_FIRMWARE_BAUDRATE, firmware, chip_erase)
        return ERR_OK

    def cancel_flash_firmware(self):
        self.hci_programmer.hci_port.close()
