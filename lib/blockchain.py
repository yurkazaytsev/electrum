#!/usr/bin/env python
#
# Electrum - lightweight Bitcoin client
# Copyright (C) 2012 thomasv@ecdsa.org
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.



import os
import util
import bitcoin
from bitcoin import *

def bits_to_target(bits):
    if bits == 0:
        return 0
    size = bits >> 24
    assert size <= 0x1d

    word = bits & 0x00ffffff
    assert 0x8000 <= word <= 0x7fffff

    if size <= 3:
        return word >> (8 * (3 - size))
    else:
        return word << (8 * (size - 3))

def target_to_bits(target):
    if target == 0:
        return 0
    target = min(target, MAX_TARGET)
    size = (target.bit_length() + 7) / 8
    mask64 = 0xffffffffffffffff
    if size <= 3:
        compact = (target & mask64) << (8 * (3 - size))
    else:
        compact = (target >> (8 * (size - 3))) & mask64

    if compact & 0x00800000:
        compact >>= 8
        size += 1
    assert compact == (compact & 0x007fffff)
    assert size < 256
    return compact | size << 24

MAX_BITS = 0x1d00ffff
MAX_TARGET = bits_to_target(MAX_BITS)

class Blockchain(util.PrintError):
    '''Manages blockchain headers and their verification'''
    def __init__(self, config, network):
        self.config = config
        self.network = network
        self.local_height = 0
        self.set_local_height()
        self.cur_chunk = None

    def height(self):
        return self.local_height

    def init(self):
        import threading
        if os.path.exists(self.path()):
            self.downloading_headers = False
            return
        self.downloading_headers = True
        t = threading.Thread(target = self.init_headers_file)
        t.daemon = True
        t.start()

    def verify_header(self, header, prev_header, bits):
        prev_hash = hash_header(prev_header)
        _hash = hash_header(header)
        if prev_hash != header.get('prev_block_hash'):
            raise BaseException("prev hash mismatch: %s vs %s" % (prev_hash, header.get('prev_block_hash')))
        if bitcoin.TESTNET:
            return
        if bits != header.get('bits'):
            raise BaseException("bits mismatch: %s vs %s" % (bits, header.get('bits')))
        target = bits_to_target(bits)
        if int('0x' + _hash, 16) > target:
            raise BaseException("insufficient proof of work: %s vs target %s" % (int('0x' + _hash, 16), target))

    def verify_chain(self, chain):
        first_header = chain[0]
        prev_header = self.read_header(first_header.get('block_height') - 1)
        for header in chain:
            height = header.get('block_height')
            bits = self.get_bits(height)
            self.verify_header(header, previous_header, bits)
	    prev_header = header

    def verify_chunk(self, index, data):
        self.cur_chunk = data
        self.cur_chunk_index = index
        num = len(data) / 80
        prev_header = None
        if index != 0:
            prev_header = self.read_header(index*2016 - 1)
        for i in range(num):
            raw_header = data[i*80:(i+1) * 80]
            header = deserialize_header(raw_header, index*2016 + i)
            bits = self.get_bits(header['block_height'])
            self.verify_header(header, prev_header, bits)
            prev_header = header
        self.cur_chunk = None

    def serialize_header(self, res):
        s = int_to_hex(res.get('version'), 4) \
            + rev_hex(res.get('prev_block_hash')) \
            + rev_hex(res.get('merkle_root')) \
            + int_to_hex(int(res.get('timestamp')), 4) \
            + int_to_hex(int(res.get('bits')), 4) \
            + int_to_hex(int(res.get('nonce')), 4)
        return s

    def deserialize_header(self, s):
        hex_to_int = lambda s: int('0x' + s[::-1].encode('hex'), 16)
        h = {}
        h['version'] = hex_to_int(s[0:4])
        h['prev_block_hash'] = hash_encode(s[4:36])
        h['merkle_root'] = hash_encode(s[36:68])
        h['timestamp'] = hex_to_int(s[68:72])
        h['bits'] = hex_to_int(s[72:76])
        h['nonce'] = hex_to_int(s[76:80])
        return h

    def hash_header(self, header):
        if header is None:
            return '0' * 64
        return hash_encode(Hash(self.serialize_header(header).decode('hex')))

    def path(self):
        return util.get_headers_path(self.config)

    def init_headers_file(self):
        filename = self.path()
        try:
            import urllib, socket
            socket.setdefaulttimeout(30)
            self.print_error("downloading ", bitcoin.HEADERS_URL)
            urllib.urlretrieve(bitcoin.HEADERS_URL, filename + '.tmp')
            os.rename(filename + '.tmp', filename)
            self.print_error("done.")
        except Exception:
            self.print_error("download failed. creating file", filename)
            open(filename, 'wb+').close()
        self.downloading_headers = False
        self.set_local_height()
        self.print_error("%d blocks" % self.local_height)

    def save_chunk(self, index, chunk):
        filename = self.path()
        f = open(filename, 'rb+')
        f.seek(index * 2016 * 80)
        h = f.write(chunk)
        f.close()
        self.set_local_height()

    def save_header(self, header):
        data = self.serialize_header(header).decode('hex')
        assert len(data) == 80
        height = header.get('block_height')
        filename = self.path()
        f = open(filename, 'rb+')
        f.seek(height * 80)
        h = f.write(data)
        f.close()
        self.set_local_height()

    def set_local_height(self):
        name = self.path()
        if os.path.exists(name):
            h = os.path.getsize(name)/80 - 1
            if self.local_height != h:
                self.local_height = h

    def read_header(self, block_height):
	if self.cur_chunk and (block_height // 2016) == self.cur_chunk_index:
		n = height % 2016
		h = self.cur_chunk[n * 80: (n + 1) * 80]
		h = self.deserialize_header(h)
		return h
        name = self.path()
        if os.path.exists(name):
            f = open(name, 'rb')
            f.seek(block_height * 80)
            h = f.read(80)
            f.close()
            if len(h) == 80:
                h = self.deserialize_header(h)
                return h

    def get_median_time_past(self, height):
        times = [self.read_header(h)['timestamp']
                 for h in range(max(0, height - 10), height + 1)]
        return sorted(times)[len(times) // 2]

    def get_bits(self, height):
        '''Return bits for the given height.'''
        if bitcoin.TESTNET:
            return 0
        # Difficulty adjustment interval?
        if height % 2016 == 0:
            return self.get_new_bits(height)
        prior = self.read_header(height - 1)
        bits = prior['bits']
        # Can't go below minimum, so early bail
        if bits == MAX_BITS:
            return bits
        mtp_6blocks = (self.get_median_time_past(height - 1)
                       - self.get_median_time_past(height - 7))
        if mtp_6blocks < 12 * 3600:
            return bits
        # If it took over 12hrs to produce the last 6 blocks, increase the
        # target by 25% (reducing difficulty by 20%).
        target = bits_to_target(bits)
        target += target >> 2
        return target_to_bits(target)

    def get_new_bits(self, height):
        assert height % 2016 == 0
        # Genesis
        if height == 0:
            return MAX_BITS
        first = self.read_header(height - 2016)
        prior = self.read_header(height - 1)
        prior_target = bits_to_target(prior['bits'])

        target_span = 14 * 24 * 60 * 60
        span = prior['timestamp'] - first['timestamp']
        span = min(max(span, target_span / 4), target_span * 4)
        new_target = (prior_target * span) / target_span
        return target_to_bits(new_target)

    def connect_header(self, chain, header):
        '''Builds a header chain until it connects.  Returns True if it has
        successfully connected, False if verification failed, otherwise the
        height of the next header needed.'''
        chain.append(header)  # Ordered by decreasing height
        previous_height = header['block_height'] - 1
        previous_header = self.read_header(previous_height)

        # Missing header, request it
        if not previous_header:
            return previous_height

        # Does it connect to my chain?
        prev_hash = self.hash_header(previous_header)
        if prev_hash != header.get('prev_block_hash'):
            self.print_error("reorg")
            return previous_height

        # The chain is complete.  Reverse to order by increasing height
        chain.reverse()
        try:
            self.verify_chain(chain)
            self.print_error("new height:", previous_height + len(chain))
            for header in chain:
                self.save_header(header)
            return True
        except BaseException as e:
            self.print_error(str(e))
            return False

    def connect_chunk(self, idx, hexdata):
        try:
            data = hexdata.decode('hex')
            self.verify_chunk(idx, data)
            self.print_error("validated chunk %d" % idx)
            self.save_chunk(idx, data)
            return idx + 1
        except BaseException as e:
            self.print_error('verify_chunk failed', str(e))
            return idx - 1
