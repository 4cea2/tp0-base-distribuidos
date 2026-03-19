import socket
import logging
import signal


class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._running = True
        self._client_socket = None
        signal.signal(signal.SIGTERM, self._handle_sigterm)

    def _handle_sigterm(self, signum, frame):
        self._running = False
        if self._server_socket is not None: self._server_socket.close()
        if self._client_socket is not None: self._client_socket.close()
        logging.info('action: shutdown | result: success | signal: SIGTERM')


    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        # TODO: Modify this program to handle signal to graceful shutdown
        # the server
        while self._running:
            self._client_socket = self.__accept_new_connection()
            if self._client_socket is None:
                break
            self.__handle_client_connection()

    def __handle_client_connection(self):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            # TODO: Modify the receive to avoid short-reads
            msg = self._client_socket.recv(1024).rstrip().decode('utf-8')
            addr = self._client_socket.getpeername()
            logging.info(f'action: receive_message | result: success | ip: {addr[0]} | msg: {msg}')
            # TODO: Modify the send to avoid short-writes
            self._client_socket.send("{}\n".format(msg).encode('utf-8'))
        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {e}")
        finally:
            if self._running:
                self._client_socket.close()

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        try:
            c, addr = self._server_socket.accept()
        except OSError as e:
            # The server socket is closed (probably due to SIGTERM signal), so return None to finish the server loop
            return None
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        
        return c
