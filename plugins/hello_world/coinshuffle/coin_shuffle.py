from phase import Phase
from electroncash import bitcoin


class Coin_Shuffle:
    """
    Abstract implementation of CoinShuffle in python.
    http://crypsys.mmci.uni-saarland.de/projects/CoinShuffle/coinshuffle.pdf
    """
    class Round:
        """
        A single round of the protocol. It is possible that the players may go through
        several failed rounds until they have eliminated malicious players.
        """

        def __init__(self, phase, amount, fee, sk, players, addr_new, change):

            self.__phase = phase
            #The amount to be shuffled.
            if amount >= 0:
                self.__amount = amount
            else:
                raise ValueError('wrong amount value')
            # The miner fee to be paid per player.
            if fee >= 0:
                self.__fee = fee
            else:
                raise ValueError('wrong fee value')
            # My signing private key
            self.__sk = sk
            # Which player am I?
            self.__me = None
            # The number of players.
            self.__N = None
            # The players' public keys
            if type(players) is dict:
                self.__playeres = players
                # The number of players.
                self.__N = len(players) # Do we realy need it?
            else:
                raise TypeError('Players should be stored in dict object')
            # My verification public key, which is also my identity.
            self.__vk = None #  vk = sk.VerificationKey();
            # decryption key
            self.__dk = None
            # This will contain the new encryption public keys.
            self.__encryption_keys = dict()
            # The set of new addresses into which the coins will be deposited.
            self.__new_addresses = None
            self.__addr_new = addr_new
            # My change address. (may be null).
            self.__change = change
            self.__signatures = dict()
            self.__mail_box = None

        def protocol_definition(self):

            if self.__amount <= 0:
                raise ValueError('wrong amount for transaction')

            # Phase 1: Announcement
            # In the announcement phase, participants distribute temporary encryption keys.
            self.__phase = 'Announcement'
            print ("Player " + self.__me + " begins CoinShuffle protocol " + " with " + self.__N + " players.")

begin_phase = Phase('Announcement')
amount = 1000
fee = 1
sk = 1123123124
players ={'asda':1,'asdasd':2}
addr_new = 123123
change = 12312312

z = Coin_Shuffle.Round(begin_phase, amount, fee, sk, players, addr_new, change)
z.protocol_definition()
