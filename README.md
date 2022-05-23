# Environment

Python 3.6

Flask 2.0.3

# Step

Enter the project folder:

`cd e-voting`

Download all dependencies:

`pip install -r requirements.txt`

Run a node with port 8000:

`python3 myapp/app.py -p 8000`

if a port (eg: port 8000) is in use, so you can't start project and totally have know idea what is using it, use:

`lsof -i tcp:8000`


# Reference

1. satwikkansal's tutorial 
   
   **Develop a blockchain application from scratch in Python**
   
    Original tutorial page on IBM blog is invalid now. Put the github repository here:
    https://github.com/satwikkansal/python_blockchain_app.git
   
2. pycrypto API

    https://www.dlitz.net/software/pycrypto/api/2.6/
 
3. pycrypto API
   
    https://www.dlitz.net/software/pycrypto/api/2.6/
   
4. Ethereum documents
   
   (1) https://ethereum.org/en/developers/docs/blocks/

   (2) https://ethereum.org/en/developers/docs/consensus-mechanisms/pow/
   
   (2) https://ethereum.org/en/developers/docs/consensus-mechanisms/pow/mining/
