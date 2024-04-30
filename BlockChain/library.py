import hashlib
from hashlib import sha256
import json
import time

# Eslabones de la cadena
class Block():
    def __init__(self, index, transactions, timestamp, previous_hash):
        """
        Constructor for a 'Block' class.
        : param index: The unique ID number of a block
        : transactions: List of transactions
        : timestamp: Block creatiom time
        : previous_hash: Contains the hash value of the preceding block in the chain
        """
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.current_hash = None
        self.nonce = None
        
    def compute_hash(self):
        """
        Converts the block object into a JSON string and then returns the hash value
        """
        block_string = json.dumps(self.__dict__, sort_keys = True)
        final_hash = hashlib.sha256(block_string.encode()).hexdigest()
        
        return final_hash
    

class Blockchain():
    def __init__(self, difficulty=2):
        
        self.unconfirmed_transactions = []
        self.chain = []
        self.create_genesis_block()
        self.difficulty =  difficulty # for the POW algorithm
        
    def create_genesis_block(self):
        
        genesis = Block(0, [], time.time(), "0")
        genesis.current_hash = genesis.compute_hash()
        self.chain.append(genesis)
        
    def last_block(self):
        return self.chain[-1] #last block
    
    def proof_of_work(self, block):
        
        block.nonce = 0
        generated_hash =  block.compute_hash()
        patron = '0' * self.difficulty
        
        start =  time.time()
        while not generated_hash.startswith(patron):
            block.nonce +=1
            generated_hash = block.compute_hash()
        end = time.time()
        total_time =  end-start
            
        return generated_hash, total_time
        
    def is_valid_proof(self, block, block_hs):
        patron = '0' * self.difficulty
        
        if not block_hs.startswith(patron):
            return False
        
        computed_hash = block.compute_hash()
        if computed_hash != block_hs:
            
            return False
        
        return True
    
    def append_block(self, newblock, newblock_hs):

        if (newblock.previous_hash != self.last_block().current_hash):
            return False
        
        if (self.is_valid_proof(newblock, newblock_hs) != True):
            return False
        
        newblock.current_hash = newblock_hs
        self.chain.append(newblock)
        
        return True
    
    def add_new_transaction(self, transaccion):
        
        self.unconfirmed_transactions.append(transaccion)
        
    def mine(self):
        
        if not self.unconfirmed_transactions:
            return False
        
        new_block = Block(index = self.last_block().index + 1,
                          transactions =  self.unconfirmed_transactions,
                          timestamp =  time.time(),
                          previous_hash = self.last_block().current_hash)
        
        proof, tot_time = self.proof_of_work(new_block)
        self.append_block(new_block, proof)

        self.unconfirmed_transactions = []
        return new_block