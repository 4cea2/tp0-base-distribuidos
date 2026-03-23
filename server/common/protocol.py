from common.utils import Bet

TYPE_INT = 1
TYPE_STRING = 2

class Protocol:
    def __init__(self, sock):
        self._sock = sock

    def _expect_type(self, expected: int):
        """
        Read a byte and check if it matches the expected type
        """
        t = self._sock.receive(1)[0]
        if t != expected:
            raise RuntimeError(f"Invalid type: expected {expected}, got {t}")

    def _read_int(self) -> int:
        """
        Read 4 bytes and convert to int
        """
        data = self._sock.receive(4)
        return int.from_bytes(data, byteorder="big")

    def _read_string(self) -> str:
        """
        Read 2 bytes to get the length, then read the string of that length
        """
        length_bytes = self._sock.receive(2)
        length = int.from_bytes(length_bytes, byteorder="big")
        data = self._sock.receive(length)
        return data.decode()

    def receive_bet(self) -> Bet:
        """
        Receive and deserialize a Bet using TLV format.
        ORDER:
        Agency → FirstName → LastName → Document → BirthDate → Number
        """

        self._expect_type(TYPE_INT)
        agency = self._read_int()

        self._expect_type(TYPE_STRING)
        first_name = self._read_string()

        self._expect_type(TYPE_STRING)
        last_name = self._read_string()

        self._expect_type(TYPE_INT)
        document = self._read_int()

        self._expect_type(TYPE_STRING)
        birthdate = self._read_string()

        self._expect_type(TYPE_INT)
        number = self._read_int()

        return Bet(
            agency,
            first_name,
            last_name,
            document,
            birthdate,
            number
        )