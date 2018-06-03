# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import os
import json

sys.path.insert(0, os.path.abspath('..'))

from clint.textui import puts, colored, indent
from clint.arguments import Args

from eth_utils import to_checksum_address

from utils import getWeb3, getBountiesContract, getToken, getWallet
from input import getUserInput
from ipfs import submitToIPFS

# contract = getBountyContract('mainnet')
# print(contract.functions.bounties(550).call())
#
# import ipfsapi
# ipfs = ipfsapi.connect('https://ipfs.infura.io', 5001)
# print(repr(ipfs.cat('QmSZV3GbG98pAegEq5newg9en4ioWmiCvefqjVbT79Kxkr')))
# exit(0)

# var expire_date = parseInt(expirationTimeDelta) + ((new Date().getTime() / 1000) | 0);
# var mock_expire_date = 9999999999; // 11/20/2286, https://github.com/Bounties-Network/StandardBounties/issues/25

def main(args):
    network = 'rinkeby'

    web3 = getWeb3(network)
    wallet = getWallet(0)
    bountiesContract = getBountiesContract(network)
    data = { 'ethereumAddress' : to_checksum_address(wallet.get('address')) }

    # if a json was provided, use that create the bounty, otherwise ask the user for input
    if( args.grouped.get('--json') ):
        # TODO validate json exists
        with open(args.grouped.get('--json')[0]) as f:
            data.update(json.load(f))
    else:
        data.update(getUserInput(args))

    # 1. post data to ipfs
    ipfsHash = submitToIPFS(data)

    # 2. approve token transfer (only if needed)
    if(data.get('tokenAddress') != '0x0000000000000000000000000000000000000000'):
        token = getToken(data.get('tokenAddress'))

        # TODO verify there are enough tokens for bounty
        tx = token.functions.approve(
            bountiesContract.address,
            data.get(amount),
        ).buildTransaction({
            'gasPrice': web3.toWei('5', 'gwei'),
            'gas': 70000,
            'nonce': web3.eth.getTransactionCount(data.get('ethereumAddress')),
        })



    # 3. issue and activate bounty
    # TODO verify there is enough ether to cover gas + bounty
    tx = bountiesContract.functions.issueAndActivateBounty(
        data.get('ethereumAddress'),
        data.get('expireDate'),
        ipfsHash,
        data.get('amount'),
        '0x0000000000000000000000000000000000000000',
        data.get('tokenAddress') != '0x0000000000000000000000000000000000000000',
        data.get('tokenAddress'),
        data.get('amount')
    ).buildTransaction({
        'from': data.get('ethereumAddress'),
        'value': data.get('amount'),
        'gasPrice': web3.toWei('5', 'gwei'),
        'gas': 318730,
        'nonce': web3.eth.getTransactionCount(data.get('ethereumAddress'))
    })

    signed = web3.eth.account.signTransaction(tx, private_key=wallet.get('private_key'))

    old_id = bountiesContract.functions.getNumBounties().call()
    receipt = web3.eth.waitForTransactionReceipt(web3.eth.sendRawTransaction(signed.rawTransaction)) )
    new_id = bountiesContract.function.getNumBounties().call()

    if(old_id < new_id):
        print('Bounty funded successfully!')
    else:
        print('Error funding bounty!')

if __name__ == '__main__':
    args = Args()

    with indent(4, quote=''):
        puts(colored.red('Grouped Arguments: ') + str(dict(args.grouped)))

    main(args)
