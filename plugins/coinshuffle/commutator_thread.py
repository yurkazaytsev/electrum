import socket
import threading
import Queue

class Commutator(threading.Thread):
    """
    Class for decoupling of send and recv ops.
    """
    def __init__(self, income, outcome, logger = None, buffsize = 4096, timeout = 0, switch_timeout = 0.1):
        super(Commutator, self).__init__()
        self.income = income
        self.outcome = outcome
        self.logger = logger
        self.alive = threading.Event()
        self.alive.set()
        self.socket = None
        self.frame = unichr(9166).encode('utf-8')
        self.MAX_BLOCK_SIZE = buffsize
        self.timeout = timeout
        self.switch_timeout = switch_timeout

    def debug(self, obj):
        if self.logger:
            self.logger.put(str(obj))

    def run(self):
        while self.alive.isSet():
            try:
                msg = self.income.get(True, self.switch_timeout)
                self._send(msg)
                self.debug('send!')
            except (Queue.Empty, socket.error) as e:
                try:
                    response = self._recv()
                    self.outcome.put_nowait(response)
                    self.debug('recv')
                except (Queue.Empty, socket.error) as e:
                    continue

    def join(self, timeout=None):
        self.socket.close()
        self.alive.clear()
        threading.Thread.join(self, timeout)


    def connect(self, host, port):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            self.socket.connect((host, port))
            self.socket.settimeout(self.timeout)
            self.debug('connected')
        except IOError as e:
            self.logger.put(str(e))

    def _send(self, msg):
        msg += self.frame
        self.socket.sendall(msg)

    def close(self):
        self.socket.close()
        self.debug('closed')

    def _recv(self):
        response = ''
        while response[-3:] != self.frame:
            response += self.socket.recv(self.MAX_BLOCK_SIZE)
        return response[:-3]

class Channel(Queue.Queue):
    """
    simple Queue wrapper for using recv and send
    """
    def __init__(self, switch_timeout = 0.1):
        Queue.Queue.__init__(self)
        self.switch_timeout = switch_timeout

    def send(self, message):
        # self.put(message,True,0.01)
        self.put(message,True, self.switch_timeout)
    def recv(self):
        return self.get(True)

class ChannelWithPrint(Queue.Queue):

    def send(self, message):
        print(message)
        self.put(message)

    def recv(self):
        return self.get()
