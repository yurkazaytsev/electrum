import sys
import time
from coin import Coin
from crypto import Crypto
from messages import Messages
from commutator_thread import Commutator
from commutator_thread import Channel
from commutator_thread import ChannelWithPrint
from phase import Phase
import socket
import threading
from coin_shuffle import Round
# from electroncash.bitcoin import (generator_secp256k1, point_to_ser, EC_KEY)
from ecdsa.util import number_to_string
import ecdsa
from electroncash.bitcoin import (
    generator_secp256k1, point_to_ser, public_key_to_p2pkh, EC_KEY,
    bip32_root, bip32_public_derivation, bip32_private_derivation, pw_encode,
    pw_decode, Hash, public_key_from_private_key, address_from_private_key,
    is_valid, is_private_key, xpub_from_xprv, is_new_seed, is_old_seed,
    var_int, op_push, msg_magic)

class protocolThread(threading.Thread):
    """
    This class emulate thread with protocol run
    """
    def __init__(self, host, port, network, amount, fee, sk, addr_new, change, logger = None):
        threading.Thread.__init__(self)
        self.messages = Messages()
        self.income = Channel()
        self.outcome = Channel()
        if not logger:
            self.logger = ChannelWithPrint()
        else:
            self.logger = logger
        # self.commutator = Commutator(self.income, self.outcome, logger = self.logger)
        self.commutator = Commutator(self.income, self.outcome)

        self.vk = sk.get_public_key(True)
        self.session = None
        self.number = None
        self.number_of_players = None
        self.players = {}
        self.amount = amount
        self.fee = fee
        self.sk = sk
        # self.addr_new = public_key_to_p2pkh(point_to_ser(new_pvk*G, True))
        self.addr_new = addr_new
        # self.change = public_key_to_p2pkh(point_to_ser(change_pvk*G, True))
        self.change = change
        self.deamon = True
        self.commutator.connect(host, port)
        self.network = network
        self.tx = None

    def run(self):
        self.commutator.start()
        # self.commutator.connect()
        self.messages.make_greeting(self.vk)
        msg = self.messages.packets.SerializeToString()
        self.income.send(msg)
        req = self.outcome.recv()

        self.messages.packets.ParseFromString(req)
        self.session = self.messages.packets.packet[-1].packet.session
        self.number = self.messages.packets.packet[-1].packet.number
        if self.session != '':
             # print("Player #"  + str(self.number)+" get session number.\n")
             self.logger.send("Player #"  + str(self.number)+" get session number.\n")
        # # Here is when announcment should begin
        req = self.outcome.recv()
        self.messages.packets.ParseFromString(req)
        phase = self.messages.get_phase()
        number = self.messages.get_number()
        if phase == 1 and number > 0:
            # print("player #" + str(self.number) + " is about to share verification key with " + str(number) +" players.\n")
            self.logger.send("player #" + str(self.number) + " is about to share verification key with " + str(number) +" players.\n")
            self.number_of_players = number
            #Share the keys
            self.messages.clear_packets()
            self.messages.packets.packet.add()
            self.messages.packets.packet[-1].packet.from_key.key = self.vk
            self.messages.packets.packet[-1].packet.session = self.session
            self.messages.packets.packet[-1].packet.number = self.number
            shared_key_message = self.messages.packets.SerializeToString()
            self.income.send(shared_key_message)
            messages = ''
            for i in range(number):
                messages += self.outcome.recv()
            self.messages.packets.ParseFromString(messages)
            self.players = {packet.packet.number:str(packet.packet.from_key.key) for packet in self.messages.packets.packet}
        if self.players:
            self.logger.send('player #' +str(self.number)+ " get " + str(len(self.players))+".\n")
        #
        coin = Coin(self.network)
        crypto = Crypto()
        self.messages.clear_packets()
        # log_chan = fakeLogChannel()
        begin_phase = Phase('Announcement')
        # Make Round
        protocol = Round(
            coin,
            crypto,
            self.messages,
            self.outcome,
            self.income,
            self.logger,
            self.session,
            begin_phase,
            self.amount ,
            self.fee,
            self.sk,
            self.players,
            self.addr_new,
            self.change)
        self.tx = protocol.protocol_definition()
        # time.sleep(60)
        self.commutator.join()
