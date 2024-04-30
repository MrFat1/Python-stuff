from flask import Flask, jsonify, request
import pandas as pd
from library import Blockchain
import requests
import json
import time
from library import Block
from library import Blockchain

blockchain = Blockchain()
app = Flask(__name__)
peers = set()

@app.route('/chain', methods=['GET'])
def chain():
    
    chain_dict = []
    for blok in blockchain.chain:
        chain_dict.append(blok.__dict__)
    
    response = {
        'length': len(chain_dict),
        'chain': chain_dict,
        'peers': list(peers)
    }
    
    return jsonify(response), 200

@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    
    data =  request.get_json() 
    
    if 'author' not in data and 'content' not in data:
        return "Invalid transaction data", 404
    
    data['timestamp'] = time.time()
    blockchain.add_new_transaction(data)
    
    return "Success", 201

@app.route('/mine', methods=['GET'])
def mine():

    consensus()
    backup_unconfirmed_transactions = blockchain.unconfirmed_transactions 
    if blockchain.unconfirmed_transactions:
        
        mined_block = blockchain.mine()
    
        if not consensus():
            announce_new_block(blockchain.last_block(), request)
            if peers:
                return "Block #" + str(mined_block.index) + " mined", 200
            return "Block was mined for current node, but not announced (no registered peers)", 201
    
    blockchain.unconfirmed_transactions = backup_unconfirmed_transactions
    return "Chain not the longest, block discarded. Maybe no unconfirmed transactions?", 400

@app.route('/pending_transactions', methods=['GET'])
def pending_transactions():
        
    return jsonify(blockchain.unconfirmed_transactions), 200

@app.route('/register_new_node', methods=['POST'])
def register_new_node():
    
    data =  request.get_json() 
    
    if 'new_node_address' not in data:
        return "Invalid data", 400
    
    new_node_address = data['new_node_address']
    
    if new_node_address not in peers:
        peers.add(new_node_address)
    
    return chain()

@app.route('/register_with_existing_node', methods=['POST'])
def register_with_existing_node():
    
    data =  request.get_json() 
    
    if 'node_address' not in data:
        return "Invalid data", 400
    
    # Direccion nodo existente
    host = data["node_address"]
    
    url = "http://" + host + "/register_new_node"
    
    # Nodo que quereos registrar
    data = {"new_node_address": request.host_url}
    headers = {'Content-Type': "application/json"}
    
    response = requests.post(url, json = data)
    response_data = response.json()
    
    if response.status_code == 200:
        
        response_chain = response_data['chain']
        
        for i, blok_json in enumerate(response_chain):
            
            blok = Block(blok_json["index"], 
                         blok_json["transactions"], 
                         blok_json["timestamp"], 
                         blok_json["previous_hash"])
            
            if i == 0: #Add genesis
                
                blok.current_hash = blok_json["current_hash"]
                blockchain.chain = [blok]
            
            else: #Exclude genesis
                
                blok.nonce = blok_json["nonce"]
                if not blockchain.append_block(blok, blok_json["current_hash"]):
                    return "Fallo al validar la cadena de bloques", 500
    
        peers.update(response_data["peers"])
        peers.add("http://" + host)
        
        return "Registration successful", 200
    
    else:
        
        return response.content, response.status_code
    
    
def consensus():
    
    global blockchain
    
    longest_chain = None
    current_len = len(blockchain.chain)
    
    for node in peers:
        
        url =  node + "/chain"
        
        response = requests.get(url)
        
        if response.status_code != 200:
            return False
        
        length = response.json()["length"]
        chain = response.json()['chain']
        
        if length > current_len:
            current_len = length
            longest_chain =  chain
        
    if longest_chain:
        blockchain = longest_chain
        return True
    
    return False
        
@app.route('/add_block', methods=['POST'])
def add_block():
    
    data = request.get_json()
    
    index = data['index']
    transactions = data['transactions']
    timestamp = data['timestamp']
    previous_hash = data['previous_hash']
    current_hash = data['current_hash']

    blok =  Block(index, transactions, timestamp, previous_hash)
    blok.nonce = data["nonce"]
    
    if not blockchain.append_block(blok, current_hash):
        
        return "The block was discarded", 400
    
    return "Block appended to the chain", 201


def announce_new_block(block, request):
    
    for peer in peers:
        if peer != request.host_url:
            
            data = json.dumps(block.__dict__, sort_keys=True)
            headers = {'Content-Type': 'application/json'}
            
            response = requests.post(peer + "/add_block", data=data, headers=headers)