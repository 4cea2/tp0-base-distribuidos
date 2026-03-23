import socket


class Socket:
    def __init__(self, port: str, listen_backlog: int):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.bind(('', port))
        self._sock.listen(listen_backlog)

    def send(self, data: bytes) -> None:
        self._sock.sendall(data)

    def receive(self, size: int) -> bytes:
        data = b''
        total = 0
        while total < size:
            n = self._sock.recv(size - total)
            if not n:
                raise RuntimeError("connection closed")
            data += n
            total += len(n)
        return data

    def close(self) -> None:
        self._sock.close()