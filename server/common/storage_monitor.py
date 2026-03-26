import threading
import logging
import common.utils as utils

# Monitor for the storage of bets, to protect the access to the file where the bets are stored
class StorageMonitor:
    def __init__(self):
        self._lock = threading.Lock() # Lock to protect the access to the file where the bets are stored 

    def store_batch(self, batch):
        """
        Writes a batch of bets to the file in a thread-safe way
        """
        with self._lock:
            utils.store_bets(batch)
            logging.info(f'action: almacenar_batch | result: success | cantidad: {len(batch)}')

    def load_all_bets(self):
        """
        Reads all bets from the file in a thread-safe way
        Dont protect with lock beacuse the server only reads the bets after all the agencies finished sending their bets
        """    
        return utils.load_bets()