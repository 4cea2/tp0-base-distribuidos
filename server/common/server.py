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
        # Wait for all expected agencies to connect and send their bets, and save the protocol of each agency that finished sending bets to later send the lottery results
        self._wait_for_agencies()

       # Start the lottery and determine the winners by agency
        logging.info("action: sorteo | result: success")
        winners_by_agency = self._start_lottery()

        # Notify results to each agency and close connections
        self._distribute_results(winners_by_agency)

    def _wait_for_agencies(self):
        """Find incoming connections until all expected agencies are connected"""
        while self._running and len(self._agencies_ready) < self._expected_agencies:
            self._client_socket = self.__accept_new_connection()
            if self._client_socket is None:
                break
            self.__handle_client_connection()

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

    def _start_lottery(self) -> dict[int, list[utils.Bet]]:
            """Loads all bets and filters winners grouped by agency"""
            all_bets = utils.load_bets()
            
            winners_by_agency = {agency_id: [] for agency_id in self._agencies_ready.keys()}
            
            for bet in all_bets:
                if utils.has_won(bet) and bet.agency in winners_by_agency:
                    winners_by_agency[bet.agency].append(bet)
            
            return winners_by_agency
    
    def _distribute_results(self, winners_by_agency: dict[int, list[utils.Bet]]):
        """Sends the winner list to each connected agency and closes the connection"""
        for agency_id, protocol in self._agencies_ready.items():
            winners = winners_by_agency.get(agency_id, [])
            try:
                protocol.send_winners(winners)
                logging.info(
                    f'action: enviar_ganadores | result: success | '
                    f'agencia: {agency_id} | ganadores: {len(winners)}'
                )
            except Exception as e:
                logging.error(
                    f'action: enviar_ganadores | result: fail | '
                    f'error: {str(e)} | agencia: {agency_id}'
                )
            finally:
                protocol.close_connection()