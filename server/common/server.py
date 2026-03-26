import logging
import signal
import threading
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
        self._expected_agencies = expected_agencies
        
        self._agencies_ready = {} 
        self._lock_agencies = threading.Lock()
        self._lock_storage = threading.Lock()

        self._threads = []
        signal.signal(signal.SIGTERM, self._handle_sigterm)

    def _handle_sigterm(self, signum, frame):
        self._running = False
        if self._server_socket is not None: self._server_socket.close()
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
        while self._running and len(self._threads) < self._expected_agencies:
            client_socket = self.__accept_new_connection()
            if client_socket is None:
                break
            t = threading.Thread(target=self.__handle_client_connection, args=(client_socket,))
            t.start()
            self._threads.append(t)

        # Wait for all threads to process the batchs sent from the clients and to receive the winners request (if they sent it)
        for t in self._threads:
            t.join()

        # Each theard should send the winners to each agency, but as it is implemented, the server is in charge of it

    def __handle_client_connection(self, client_socket):
        protocol = Protocol(client_socket)
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
                    self._safe_store_bets(batch)

                protocol.send_response(ACK_SUCCESS_BATCH)
                if len(batch) == 0: 
                        # Notification that the client finished sending bets
                        logging.info("action: client_finished | result: success")
                        break
            except Exception as e:
                logging.error(f'action: apuesta_recibida | result: fail | cantidad: {len(batch)}')
                protocol.send_response(ACK_ERROR_BATCH)
        
        if protocol.receive_winners_request():
            logging.info(f'action: recibir_consulta_ganadores | result: success | agencia: {agency_id}')
            self._safe_register_agency(agency_id, protocol)
        else:
            logging.error(f'action: recibir_consulta_ganadores | result: fail | agencia: {agency_id}')
            protocol.close_connection()

    def _safe_store_bets(self, batch):
        """Encapsula la escritura en disco protegiéndola con un Lock"""
        with self._lock_storage:
            utils.store_bets(batch)
            logging.info(f'action: apuesta_guardada | result: success | cantidad: {len(batch)}')

    def _safe_register_agency(self, agency_id, protocol):
        """Encapsula el acceso al diccionario compartido"""
        with self._lock_agencies:
            self._agencies_ready[agency_id] = protocol
            logging.info(f'action: agencia_lista | result: success | agencia: {agency_id} | agencias_listas: {len(self._agencies_ready)}/{self._expected_agencies}')

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