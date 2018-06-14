
"""
@author: Pooja Sharma
"""

# Create a Cryptocurrency

# Importing the libraries
import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests  # to catch the right nodes when we check all the nodes in the decentralized blockchain have indeed the same chain, where consensus may need to apply
from uuid import uuid4 # to create an address for each node in the network
from urllib.parse import urlparse # to parse the url of each of the nodes

# Part 1 - Building a blockchain

class Blockchain:
    def __init__(self):     #self is the object here and we are initializing our blockchain with two variables
        # initialize our chain with empty list
        self.chain = []
        
        # to transform our general blockchain into a cryptocurrency, there has to be some transactions,
        # here we create a separate list of transactions because transactions are not born or included into a block until the block is mined
        # these transactions are kept separate and during mining they are included in the block and removed from the transaction list
        # initialize this list as empty list        
        self.transactions = []
        
        # we will use this create_block function right after the block is mined
        # this create_block function creates the genesis block
        self.create_block(proof=1,previous_hash='0')
        
        # to implement the consensus which makes sure that all the nodes in the decentralized network contain the same chain at any point of time whenever a new block is added to the chain 
        # to implement the consensus, we need nodes having particular address
        # nodes don't need to be ordered, so instead of list, we are initializing nodes with empty set
        self.nodes = set()
        
    def create_block(self,proof,previous_hash):
                                                        
        block = {
                    'index':len(self.chain) + 1,
                    'timestamp' : str(datetime.datetime.now()),  # we made timestamp a string so prevent any issue while using in json and datetime.datetime.now() is library.module.function
                    'proof' : proof,
                    'previous_hash' : previous_hash,
                    'transactions' : self.transactions
                }
        # after transactions have been added into the block, transactions list needs to be emptied, we cannot add same transactions in more than one block
        self.transactions = []
        self.chain.append(block)    # we append our above created block to the chain
        return block # to display the information of this block, we need to return the block here
    
    def get_previous_block(self):
        return self.chain[-1]   # -1 gives the last index of the chain
    
    def proof_of_work(self,previous_proof):
        new_proof = 1
        check_proof = False
        while(check_proof is False):
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof
    
    def hash(self,block):
        encoded_block = json.dumps(block,sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self,chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index +=1
        return True
    
    #this defines the certain format of the transaction including the sender, the receiver and the amount exchanged 
    # and at the same time append the transaction to the list of transactions before they are integrated to the block
    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({'sender' : sender,
                                  'receiver' : receiver,
                                  'amount' : amount})
        # we will return the index of the block in which these transactions are added/appended
        # most probably transaction will be added to the new block, so we will return the index of the new block
        # by getting the index of the last block and adding 1 to it
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1
    
    # this function will add a node to the set of nodes
    # this takes the address of the nodes as its argument
    # first the address of the node needs to be parsed which will return the parsed address of the node
    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
        
    # this method will replace the longer chain with the shorter one
    def replace_chain(self):
        # this network is the set of nodes all around the globe
        network = self.nodes
        longest_chain = None
        # currently max length is the length of the current chain
        max_length = len(self.chain)
        # all the nodes in the network should be checked which one has the longest chain
        for nodes in network:
            # we will call the get_chain() method on every node in the for loop to get the chain and its length but that function
            # is not inside Blochain class and it's an api call, so here we used requests.get() method
            response = requests.get('http:///{nodes}/get_chain')
            if response.status_code == 200:
                # our response is in json format, so to access any property of that, we'll first use json() function
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        else:
            return False
                
        
            
            

# Part 2 - Mining a blockchain
        
# Creating a Web App
app = Flask(__name__)

# Creating an address for the node on port 5000
# whenever a block is mined having some transactions, a transaction fee is given to the miner
# which creates a new transaction from this node address to the miner address, so we need node_address
# also add_node() takes the node_address as its argument
node_address = str(uuid4()).replace('-','')

# Creating a Blockchain
blockchain = Blockchain()

# Mining a new block
@app.route('/mine_block',methods=['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof'];
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transaction(sender=node_address,receiver='Pooja Sharma',amount=1)
    block = blockchain.create_block(proof,previous_hash)
    response = {
            'message' : 'Congratulations! You just mined a block',
            'index' : block['index'],
            'timestamp' : block['timestamp'],
            'proof' : block['proof'],
            'previous_hash' : block['previous_hash'],
            'transactions' : block['transactions']
                }
    return jsonify(response), 200

# Getting the full blockchain
@app.route('/get_chain', methods=['GET'])
def get_chain():
    response = {
                'chain': blockchain.chain,
                'length' : len(blockchain.chain)
            }
    return jsonify(response),200

# to know if our chain is valid
@app.route('/is_valid', methods=['GET'])
def is_valid():
    result = blockchain.is_chain_valid(blockchain.chain)
    if result:
        response = {'message' : 'Everything is good with the blockchain'}
    else:
        response = {'message':'Something is wrong in the blockchain'}
    return jsonify(response),200

# Adding the new transactions in the blockchain
@app.route('/add_transaction', methods=['POST'])
def add_transactions():
    json = request.get_json()
    transaction_keys = ['sender','receiver','amount']
    if not all (key in json for key in transaction_keys):
        return 'Some elements of this transaction is missing',400
    index = blockchain.add_transaction(json['sender'],json['receiver'],json['amount'])
    response = {'message': f'This transaction will be added to the Block {index}'}
    return jsonify(response),201




# Part 3 - Decentralizing the blockchain

# connecting new nodes
@app.route('/connect_node', methods=['POST'])
def connect_node():
    # get the request of posting new node in the network through get_json() which returns a json file containing all the nodes in the network includin the one we are going to connect
    json = request.get_json()
    # connect the new node to all the other nodes in the network
    # add_node() will add all the nodes of the json file to our Blockchain network
    # the json file contains the addresses of the all the nodes in the network under the nodes key, so we will get the addresses first into the nodes variable
    nodes = json.get('nodes')
    if nodes is None:
        return 'No node', 400
    # now if there exists some addresses in the list, we will loop through it and add them
    for node in nodes:
        blockchain.add_node(node)
    response = {'message' : 'All the nodes are now connected. Jazcoin Blockchain now contains the following nodes',
                'total_nodes' : list(blockchain.nodes)}
    return jsonify(response),201

    
# replace the chain that is not up-to-date by the longest chain in the network
@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message' : 'The nodes has different chains so the chain was replaced by the longest chain',
                    'new_chain' : blockchain.chain}
    else:
        response = {'message':'All good. The chain is the largest one'
                    'actual_chain' : blockchain.chain}
    return jsonify(response),200

    
app.run(host='0.0.0.0', port = 5001)
    
    