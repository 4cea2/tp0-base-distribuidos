import socket


class Socket:
    def __init__(self, port: int = None, listen_backlog: int = None, sock=None):
        if sock is not None:
            # Socket is already created, use it
            self._sock = sock
        else:
            # Socket is not created, create it
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
    
    def accept(self):
        c, addr = self._sock.accept()
        return Socket(sock=c), addr

    def close(self) -> None:
        self._sock.close()