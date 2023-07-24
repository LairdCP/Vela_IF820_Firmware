import logging
from common.DvkProbe import DvkProbe
from common.HciSerialPort import HciSerialPort

HCI_DEFAULT_BAUDRATE = 115200

ERR_OK = 0
ERR_BOARD_NOT_FOUND = -1


class If820Board(DvkProbe):

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

            board.hci_port = probe.ports[0].device
            board.puart_port = probe.ports[1].device
            boards.append(board)
        return boards

    @staticmethod
    def get_board_by_com_port(com_port: str):
        """Get a board that uses the specified COM port.

        Returns:
            If820Board: IF820 board or None if not found
        """
        for board in If820Board.get_connected_boards():
            if board.hci_port == com_port or board.puart_port == com_port:
                return board
        return None

    def __init__(self):
        self._probe = super().__init__()
        self._hci_port = ""
        self._puart_port = ""

    @property
    def probe(self):
        return self._probe

    @probe.setter
    def probe(self, p: DvkProbe):
        self._probe = p

    @property
    def hci_port(self):
        return self._hci_port

    @hci_port.setter
    def hci_port(self, p: str):
        self._hci_port = p

    @property
    def puart_port(self):
        return self._puart_port

    @puart_port.setter
    def puart_port(self, p: str):
        self._puart_port = p

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

        hci = HciSerialPort()
        logging.debug(f"Opening HCI port {board.hci_port}")
        hci.open(board.hci_port, HCI_DEFAULT_BAUDRATE)
        board.probe.open()
        board.probe.reset_device()
        board.probe.close()
        hci.close()
        return ERR_OK