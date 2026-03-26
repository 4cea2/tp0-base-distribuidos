import logging
import signal

from common.socket import Socket
from common.agencies_monitor import AgenciesMonitor
from common.storage_monitor import StorageMonitor
from common.client_handler import ClientHandler
import threading
import common.utils as utils

class Server:
    def __init__(self, port, listen_backlog, expected_agencies):
        self._server_socket = Socket(port, listen_backlog)
        self._running = True

        self._expected_agencies = expected_agencies # Number of expected agencies to connect and send their bets
        self._agencies_monitor = AgenciesMonitor()
        self._storage_monitor = StorageMonitor()
        self._clients_handler = [] # List to keep track of the client handler threads, to later join them before finishing the server

        self._barrier_bets_stored = threading.Barrier(expected_agencies + 1) 
        self._barrier_for_results = threading.Barrier(expected_agencies + 1)

        signal.signal(signal.SIGTERM, self._handle_sigterm)

    def _handle_sigterm(self, signum, frame):
        self._running = False
        if self._server_socket is not None: self._server_socket.close()
        logging.info('action: shutdown | result: success | signal: SIGTERM')

    def run(self):
        # Wait for all expected agencies to connect and send their bets, and save the protocol of each agency that finished sending bets to later send the lottery results
        self._wait_for_agencies()

        self._barrier_bets_stored.wait() # Wait until all bets are stored before starting the lottery, to make sure all bets are included in the lottery

       # Start the lottery and determine the winners by agency
        logging.info("action: sorteo | result: success")
        winners_by_agency = self._start_lottery()

        # Notify results to each agency and close connections
        self._distribute_results(winners_by_agency)

        # Join the client handler threads to make sure all resources are released before finishing the server
        for client_handler in self._clients_handler:
            client_handler.join()

    def _wait_for_agencies(self):
        """Find incoming connections until all expected agencies are connected"""
        while self._running and len(self._clients_handler) < self._expected_agencies:
            client_socket = self.__accept_new_connection()
            if client_socket is None:
                # The server socket was closed, probably due to SIGTERM signal, so break the loop to finish the server
                break
            client_handler = ClientHandler(client_socket, 
                                           self._agencies_monitor, 
                                           self._storage_monitor, 
                                           self._barrier_bets_stored,
                                           self._barrier_for_results)
            client_handler.start()
            self._clients_handler.append(client_handler)

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
            
            winners_by_agency = {agency_id: [] for agency_id in self._agencies_monitor.get_agencies_registered()}
            
            for bet in all_bets:
                if utils.has_won(bet) and bet.agency in winners_by_agency:
                    winners_by_agency[bet.agency].append(bet)
            
            return winners_by_agency
    
    def _distribute_results(self, winners_by_agency: dict[int, list[utils.Bet]]):
        self._agencies_monitor.distribute_results(winners_by_agency)
        self._barrier_for_results.wait() 
