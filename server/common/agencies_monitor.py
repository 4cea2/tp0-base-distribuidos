import threading
import logging

# Monitor for the agencies that sent the winners request, to later send them the lottery results when they are available
class AgenciesMonitor:
    def __init__(self):
        self._winners_for_registered_agencies = {}  # Winner bets for each agency that sent the winners request
        self._lock = threading.Lock() # Lock to protect the access to the _winners_for_registered_agencies dictionary
    
    def register_agency(self, agency_id):
        """
        Registers an agency in a thread-safe way when it sends the winners request
        """
        with self._lock:
            self._winners_for_registered_agencies[agency_id] = []
            logging.info(f'action: agencia_registrada_para_resultados | result: success | agencia: {agency_id}')
    
    def distribute_results(self, winners_by_agency):
        """
        Saves the winners for each agency that sent the winners request        
        """
        for agency_id, winners in winners_by_agency.items():
            if agency_id in self._winners_for_registered_agencies:
                self._winners_for_registered_agencies[agency_id] = winners
                logging.info(f'action: resultados_distribuidos | result: success | agencia: {agency_id} | ganadores: {len(winners)}')
            else:
                logging.warning(f'action: resultados_distribuidos | result: fail | agencia: {agency_id} | error: agencia no registrada para recibir resultados')
    
    def get_winners(self, agency_id):
        """"
        Returns the winners for a specific agency
        """
        return self._winners_for_registered_agencies.get(agency_id)
    
    def get_agencies_registered(self):
        """
        Returns the agencies that sent the winners request
        """
        return self._winners_for_registered_agencies.keys()