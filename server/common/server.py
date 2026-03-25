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
    def __init__(self, port, listen_backlog, expected_agencies):
        self._server_socket = Socket(port, listen_backlog)
        self._running = True
        self._client_socket = None
        self._expected_agencies = expected_agencies
        self._agencies_ready = {} # dict (agency_id -> protocol)
        signal.signal(signal.SIGTERM, self._handle_sigterm)

    def _handle_sigterm(self, signum, frame):
        self._running = False
        if self._server_socket is not None: self._server_socket.close()
        if self._client_socket is not None: self._client_socket.close()
        logging.info('action: shutdown | result: success | signal: SIGTERM')


    def run(self):
        # Find incoming connections until all expected agencies are connected or a termination signal (SIGTERM) is received
        while self._running and self._expected_agencies != len(self._agencies_ready):
            self._client_socket = self.__accept_new_connection()
            if self._client_socket is None:
                break
            self.__handle_client_connection()

        # Start the lottery
        logging.info("action: sorteo | result: success")
        bets = utils.load_bets() # Función de la cátedra

        # Find the winners for each agency that sent the notification that they finished sending bets
        winners_by_agency = {}
        for agency_id in self._agencies_ready.keys():
            winners_by_agency[agency_id] = []
        for bet in bets:
            if utils.has_won(bet):
                winners_by_agency[bet.agency].append(bet)

        # Send the winners to each agency that connected and notified that it finished sending bets, and then close the connection with each of them
        for agency_id, protocol in self._agencies_ready.items():
            try:
                protocol.send_winners(winners_by_agency[agency_id])
                logging.info(f'action: enviar_ganadores | result: success | agencia: {agency_id} | ganadores: {len(winners_by_agency[agency_id])}')
            except Exception as e:
                logging.error(f'action: enviar_ganadores | result: fail | error: {str(e)} | agencia: {agency_id}')
            # Close the connection with the agency after sending the winners, since no more messages are expected from it
            protocol.close_connection()

    def __handle_client_connection(self):
        protocol = Protocol(self._client_socket)
        agency_id = None
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
                    agency_id = batch[0].agency
                    utils.store_bets(batch)

                protocol.send_response(ACK_SUCCESS_BATCH)
                if len(batch) == 0: 
                        # Notification that the client finished sending bets, so save its protocol to later send the lottery results
                        logging.info("action: client_finished | result: success")
                        self._agencies_ready[agency_id] = protocol
                        break
            except Exception as e:
                logging.error(f'action: apuesta_recibida | result: fail | cantidad: {len(batch)}')
                protocol.send_response(ACK_ERROR_BATCH)

        

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
