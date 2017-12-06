# from test.fake_wallet import wallet
from client import protocolThread
from coin import Coin
from commutator_thread import ChannelWithPrint
from electroncash.bitcoin import (is_address, regenerate_key)
import unittest

wallet = [
    {'address': '1NeWMaGLz6rteWM53iCxCNajunE59825Vt',
     'private': 'Kx4u7q3zNvKvob1H71rqJCah3h5NqcFmR6g3N8YmFh6BS1vKCzb2',
     'public': '02a553fa746260f4c0fd136c83f6a5a7c5edb1f9e46181c6b1ce6644e040bda79c'},
    {'address': '17gbtfRtKYP13hgTVXS7i4ou7RMyY9EUJi' ,
     'private': 'KyawtwwtviSMCykUstebBX43MMDSiYxuyX4caTrM3CQ7B9pBwZa9',
     'public': '03deaa3f581b92826823472ac33ec8c616d0633d3fb0e3f8176c65ed5a6952fe5c'},
    {'address': '18GnhPGJM4qiQxYyNMtu9ECJUwoALH9mpW' ,
     'private': 'KzKEngkKtQXnshw55HJav3PCCvuZbpWE3KVLPgnB6ZkxZyX74GpR',
     'public': '0328fdaada466891faba85fc69cbcdd315770c2ee532a8ebcab0d04ebfe1a5d5be'},
    {'address': '1Ch36FWbAwxpKgVb3KCuiJ5upkcCw3S2nZ' ,
     'private': 'KwSQrpuHGFkSofVYBkJ5DdtUf3QXqo41Jx27CyG9Kh1YNzmmWcZn',
     'public': '0330194ca849e5d918f1f74dc2b4c6378c8a37a6373125240f340f146a6a721fc0'},
     {'address': '1Di11fHZb2JgcYPEkkdVztJd3DZf6PfHkC' ,
      'private': 'KzuqtjDQgYjA1nwNkwBgwdbtm6nfo5k8C47WuE3SLyH9HEzskFiR',
      'public': '03c68f4a834cca492e4cfbfb7beeb70ae064c2ab8c116dedb36bfbe2b966eccf93'}
]

utxos = [
    {'address': '1NeWMaGLz6rteWM53iCxCNajunE59825Vt',
     'utxo': {'tx_hash': '371580e94d1d804e408e3df70011155d71c9e94272b441285d07c81fcb3a101f',
              'tx_pos': 3,
              'value': 17000,
              'height': 504983}
     },
    {'address': '17gbtfRtKYP13hgTVXS7i4ou7RMyY9EUJi' ,
     'utxo':{'tx_hash': 'd5fa351d731f4c8248beed455663afe0a8b7e4c69180e8e9bda2e9d9ef876493',
             'tx_pos': 0,
             'value': 1000,
             'height': 506451}},
    {'address': '18GnhPGJM4qiQxYyNMtu9ECJUwoALH9mpW' ,
     'utxo': {'tx_hash': 'a2e85c628edb9ab4b29e55b17f69ab2af652e186ec38eb650381e87c370a7721',
              'tx_pos': 0,
              'value': 4000,
              'height': 505489} },
    {'address': '1Ch36FWbAwxpKgVb3KCuiJ5upkcCw3S2nZ' ,
     'utxo': {'tx_hash': u'a2e85c628edb9ab4b29e55b17f69ab2af652e186ec38eb650381e87c370a7721',
              'tx_pos': 1,
              'value': 4000,
              'height': 505489}},
     {'address': '1Di11fHZb2JgcYPEkkdVztJd3DZf6PfHkC' ,
      'utxo': {'tx_hash': u'a2e85c628edb9ab4b29e55b17f69ab2af652e186ec38eb650381e87c370a7721',
               'tx_pos': 2,
               'value': 4000,
               'height': 505489}}
]


class network(object):

    def synchronous_get(self, *request):
        command, address = request
        print(request)
        # if command == 'blockchain.address.listunspent':
        #     return [utxo for utxo in utxos if utxo in address]

test_coin = Coin(network)

class EnvironmentTest(unittest.TestCase):

    def test_00_is_addresses(self):
      for coin in wallet:
          assert is_address(coin['address'])

    def test_01_is_public_keys_form_private(self):
      for coin in wallet:
          sk = regenerate_key(coin['private'])
          assert sk.get_public_key() == coin['public']

    # def test_02_is_fake_network_works(self):
    #     for coin in wallet:
    #         assert test_coin.sufficient_funds(coin['address'], 100)
