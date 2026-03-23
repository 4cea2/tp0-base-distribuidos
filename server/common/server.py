import socket
import logging
import signal
from common.socket import Socket
from common.protocol import Protocol
import common.utils as utils

class Server:
    def __init__(self, port, listen_backlog):
        self._server_socket = Socket(port, listen_backlog)
        self._running = True
        self._client_socket = None
        signal.signal(signal.SIGTERM, self._handle_sigterm)

    def _handle_sigterm(self, signum, frame):
        self._running = False
        if self._server_socket is not None: self._server_socket.close()
        if self._client_socket is not None: self._client_socket.close()
        logging.info('action: shutdown | result: success | signal: SIGTERM')


    def run(self):
        # TODO: Modify this program to handle signal to graceful shutdown
        # the server
        while self._running:
            self._client_socket = self.__accept_new_connection()
            if self._client_socket is None:
                break
            self.__handle_client_connection()
        self._server_socket.close()

    def __handle_client_connection(self):
        protocol = Protocol(self._client_socket)
        try:
            bet = protocol.receive_bet()
            logging.info(f'action: receive_bet | result: success | bet: {bet.__dict__}')
            utils.store_bets([bet])
            logging.info(f'action: store_bet | result: success | bet: {bet.__dict__}')
            protocol.send_confirmation_bet()
        except OSError as e:
            logging.error("action: receive_bet | result: fail | error: {e}")
        finally:
            if self._running:
                self._client_socket.close()

    def __accept_new_connection(self):
        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        try:
            c, addr = self._server_socket.accept()
        except OSError as e:
            # The server socket is closed (probably due to SIGTERM signal), so return None to finish the server loop
            return None
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        
        return c
