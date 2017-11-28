from electroncash.bitcoin import (
    MySigningKey, SECP256k1,
    generator_secp256k1, point_to_ser, public_key_to_p2pkh, EC_KEY,
    bip32_root, bip32_public_derivation, bip32_private_derivation, pw_encode,
    pw_decode, Hash, public_key_from_private_key, address_from_private_key,
    is_valid, is_private_key, xpub_from_xprv, is_new_seed, is_old_seed,
    var_int, op_push, pubkey_from_signature, msg_magic, TYPE_ADDRESS, SecretToASecret, number_to_string)
from electroncash.transaction import Transaction, int_to_hex
import ecdsa
import hashlib

class Coin(object):
    """
    it is a class for interaction with blockchain interaction
    will be fake functions for now
    """

    def __init__(self, network):
        self.network = network

    def sufficient_funds(self, address, amount):
        """
        System should check for sufficient funds here.
        amount here is satoshis
        """
        unspent_list = self.network.synchronous_get(('blockchain.address.listunspent', [address]))
        values = [uxto['value'] for uxto in unspent_list]
        return len([i for i in values if i > amount]) > 0

    def address(self, vk):
        return public_key_to_p2pkh(vk.decode('hex'))

    def get_first_sufficient_utxo(self, address, amount):
        # it takes a list of coins from address,
        # filter coins for sufficietn ammount
        # takes first coin.
        # protocol doesn't specify which coin form address is used for transaction.
        # It is supposed to have single output for address to be shuffled
        coins = self.network.synchronous_get(('blockchain.address.listunspent', [address]))
        coins = [coin for coin in coins if coin['value'] >= amount ]
        if coins:
            return coins[0]
        else:
            return None

    def make_unsigned_transaction(self, amount, fee, inputs, outputs, changes):
        # get coins for inputs
        coins = {vk : self.get_first_sufficient_utxo(inputs[vk], amount) for vk in inputs}
        # add type information
        # add 'signature'
        for vk in coins:
            coins[vk]['type'] = 'p2pkh'
            coins[vk]['address'] = self.address(vk)
            coins[vk]['pubkeys'] = [vk]
            coins[vk]['x_pubkeys'] = [vk]
            coins[vk]['prevout_hash'] = coins[vk]['tx_hash']
            coins[vk]['prevout_n'] = coins[vk]['tx_pos']
            coins[vk]['signatures'] = [None]
            coins[vk]['num_sig'] = 1
        # Here I use sorted to have a idential inputs order for every player
        tx_inputs = [coins[vk] for vk in sorted(coins)]
        # make outputs
        tx_outputs = [(TYPE_ADDRESS, output, amount) for output in outputs ]
        # make transaction from inputs and outputs
        tx = Transaction.from_io(tx_inputs, tx_outputs)
        # make changes
        tx_changes = [(TYPE_ADDRESS, changes[vk], coins[vk]['value'] - amount - fee)  for vk in changes]
        tx.add_outputs(tx_changes)
        return tx

    def get_transaction_signature(self, tx, sk):
        vk = sk.get_public_key(True)
        txin = filter(lambda x: vk in x['pubkeys'], tx.inputs())
        if txin:
            tx_num = tx.inputs().index(txin[0])
            pre_hash = Hash(tx.serialize_preimage(tx_num).decode('hex'))
            private_key = MySigningKey.from_secret_exponent(sk.secret, curve = SECP256k1)
            public_key = private_key.get_verifying_key()
            sig = private_key.sign_digest_deterministic(pre_hash, hashfunc=hashlib.sha256, sigencode = ecdsa.util.sigencode_der)
            assert public_key.verify_digest(sig, pre_hash, sigdecode = ecdsa.util.sigdecode_der)
            return sig.encode('hex') + int_to_hex(tx.nHashType() & 255, 1)
        return ''

    def add_transaction_signatures(self, tx, signatures):
        for i, txin in enumerate(tx._inputs):
            tx._inputs[i]['signatures'] = [signatures.get(tx._inputs[i]['pubkeys'][0])]
            tx.raw = tx.serialize()
        return tx

    def check_double_spend(t):
        "Double Spend Check should go here"
        return true

    def verify_signature(self, sig, message, vk):
        pk, compressed = pubkey_from_signature(sig,Hash(msg_magic(message)))
        address_from_signature = public_key_to_p2pkh(point_to_ser(pk.pubkey.point,compressed))
        address_from_vk = self.address(vk)
        return address_from_signature == address_from_signature
