import socket
import logging
import signal
from common.socket import Socket
from common.protocol import Protocol
import common.utils as utils

from common.protocol import (
    ACK_SUCCESS_BATCH,
    ACK_ERROR_BATCH
)

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
        while self._running:
            self._client_socket = self.__accept_new_connection()
            if self._client_socket is None:
                break
            self.__handle_client_connection()
        self._server_socket.close()

    def __handle_client_connection(self):
        protocol = Protocol(self._client_socket)
        while self._running:
            try:
                batch = protocol.receive_batch()
            except (RuntimeError, ConnectionError): 
                # Client closed connection
                logging.info("action: connection_closed | result: success")
                break
            try:
                logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(batch)}')
                if len(batch) > 0:
                    utils.store_bets(batch)

                protocol.send_response(ACK_SUCCESS_BATCH)
                if len(batch) == 0: 
                        # Client finished sending batchs and closed connection
                        logging.info("action: client_finished | result: success")
                        break
            except Exception as e:
                logging.error(f'action: apuesta_recibida | result: fail | cantidad: {len(batch)}')
                protocol.send_response(ACK_ERROR_BATCH)
            
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
