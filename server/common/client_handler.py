import threading
import logging
from common.protocol import Protocol, ACK_SUCCESS_BATCH, ACK_ERROR_BATCH

# Thread that handles the communication with a single client, receives the bets batches and the winners request, 
# and sends the winners to the client when they are available
class ClientHandler(threading.Thread):
    def __init__(self, client_socket, agencies_monitor, storage_monitor, barrier_bets_stored, barrier_for_results):
        super().__init__()
        self._protocol = Protocol(client_socket) # Protocol to handle the communication with the client
        self._agencies_monitor = agencies_monitor # Monitor to register the agencies that sent the winners request
        self._storage_monitor = storage_monitor # Monitor to store the bets batches in a thread-safe way
        self._barrier_bets_stored = barrier_bets_stored # Barrier to wait until all agencies finished sending bets before starting the lottery
        self._barrier_for_results = barrier_for_results # Barrier to wait until the lottery results are distributed
        self._running = True # Flag to indicate if the client handler is still running

    def run(self):
        """
        Handle the communication with the client
        """
        try:
            agency_id = self._process_batches()
            self._handle_winners_request(agency_id)
        except Exception as e:
            logging.error(f"action: client_handler | result: fail | error: {e}")

    def _process_batches(self):
        """
        Receives the bets batches from the client until the client finished sending bets, and stores them
        Returns the agency id of the bets received
        """
        agency_id = None
        while self._running:
            try:
                batch = self._protocol.receive_batch()
            except (RuntimeError, ConnectionError): 
                # Client closed connection
                logging.info("action: connection_closed | result: success")
                break
            try:
                logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(batch)}')
                if len(batch) > 0:
                    agency_id = batch[0].agency
                    self._storage_monitor.store_batch(batch)

                self._protocol.send_response(ACK_SUCCESS_BATCH)
                
                if len(batch) == 0: 
                    # Notification that the client finished sending bets
                    logging.info("action: client_finished | result: success")
                    break
            except Exception as e:
                logging.error(f'action: apuesta_recibida | result: fail | cantidad: {len(batch)}')
                self._protocol.send_response(ACK_ERROR_BATCH)

        return agency_id


    def _handle_winners_request(self, agency_id):
        """
        Receives the winners request from the client and registers the agency in the monitor
        Then, waits until the lottery results are distributed and sends the winners to the client
        """
        if not self._running:
            return

        if self._protocol.receive_winners_request():
            logging.info(f'action: recibir_consulta_ganadores | result: success | agencia: {agency_id}')
            self._agencies_monitor.register_agency(agency_id)
        else:
            logging.error(f'action: recibir_consulta_ganadores | result: fail | agencia: {agency_id}')
            self._protocol.close_connection()
        
        self._barrier_bets_stored.wait() 

        self._barrier_for_results.wait() 
        
        winners = self._agencies_monitor.get_winners(agency_id)

        try:
            self._protocol.send_winners(winners)
            logging.info(f'action: enviar_ganadores | result: success | agencia: {agency_id} | ganadores: {len(winners)}')
        except Exception as e:
            logging.error(f'action: enviar_ganadores | result: fail | agencia: {agency_id} | error: {e}')
        finally:            
            self._protocol.close_connection()
    