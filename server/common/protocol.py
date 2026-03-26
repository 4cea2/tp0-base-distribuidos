from common.utils import Bet

TYPE_INT = 1
TYPE_STRING = 2
TYPE_WINNERS_REQUEST = 3

ACK_SUCCESS_BATCH = 0
ACK_ERROR_BATCH = 1

TYPE_SIZE = 1
INT_SIZE = 4
STRING_LENGTH_SIZE = 2

BATCH_COUNT_SIZE = 4

class Protocol:
    def __init__(self, sock):
        self._sock = sock

    def _expect_type(self, expected: int):
        """
        Read a byte and check if it matches the expected type
        """
        t = self._sock.receive(TYPE_SIZE)[0]
        if t != expected:
            raise RuntimeError(f"Invalid type: expected {expected}, got {t}")

    def _read_int(self) -> int:
        """
        Read 4 bytes and convert to int
        """
        data = self._sock.receive(INT_SIZE)
        return int.from_bytes(data, byteorder="big")

    def _read_string(self) -> str:
        """
        Read 2 bytes to get the length, then read the string of that length
        """
        length_bytes = self._sock.receive(STRING_LENGTH_SIZE)
        length = int.from_bytes(length_bytes, byteorder="big")
        data = self._sock.receive(length)
        return data.decode()

    def _receive_bet(self) -> Bet:
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

    def receive_batch(self) -> list[Bet]:
        """
        Receive the batch size and then each bet in the batch.
        """
        count_bytes = self._sock.receive(BATCH_COUNT_SIZE)
        batch_size = int.from_bytes(count_bytes, byteorder="big")
        
        bets = []
        for _ in range(batch_size):
            bets.append(self._receive_bet())
        return bets
        

    def send_response(self, code: int):
        """ 
        Send a single byte response code
        """
        self._sock.send(bytes([code]))

    def send_winners(self, winners: list[Bet]):
        """
        Send the batch size and then each winning bet in the batch.
        """
        count_bytes = len(winners).to_bytes(BATCH_COUNT_SIZE, byteorder="big")
        self._sock.send(count_bytes)
        for bet in winners:
            self._send_bet(bet)

    def _send_int(self, value: int):
        """
        Send an integer in TLV-like format
        """
        self._sock.send(bytes([TYPE_INT]))
        self._sock.send(value.to_bytes(INT_SIZE, byteorder="big"))


    def _send_string(self, value: str):
        """"
        Send a string in TLV-like format
        """
        encoded = value.encode()
        self._sock.send(bytes([TYPE_STRING]))
        self._sock.send(len(encoded).to_bytes(STRING_LENGTH_SIZE, byteorder="big"))
        self._sock.send(encoded)


    def _send_bet(self, bet: Bet):
        """
        Send a Bet in TLV-like format, following the same order as _receive_bet
        """
        self._send_int(bet.agency)
        self._send_string(bet.first_name)
        self._send_string(bet.last_name)
        self._send_int(int(bet.document))
        self._send_string(bet.birthdate.isoformat())
        self._send_int(bet.number)

    def receive_winners_request(self) -> bool:
        """
        Block until we receive the winners request byte (3)
        """
        try:
            data = self._sock.receive(TYPE_SIZE)
            if not data:
                return False
            
            operation_code = data[0]
            if operation_code == TYPE_WINNERS_REQUEST:
                return True
            
            return False
        except (RuntimeError, ConnectionError):
            return False

    def close_connection(self):
        self._sock.close()