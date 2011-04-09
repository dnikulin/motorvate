# Copyright (c) 2010-2011 Dmitri Nikulin
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import struct

from tools import report

from pymodbus.client.sync import ModbusTcpClient
from pymodbus.constants import Defaults

from pymodbus.register_read_message import ReadInputRegistersRequest
from pymodbus.register_write_message import WriteSingleRegisterRequest

class ControlLink(object):
    def __init__(self, host, port=Defaults.Port):
        self.conn = ModbusTcpClient(host, port)
        self.conn.connect()

    def read(self, offset):
        req = ReadInputRegistersRequest(offset)
        return long(self.conn.execute(req).value)

    def write(self, offset, value):
        req = WriteSingleRegisterRequest(offset, value)
        nvalue = self.conn.execute(req).value
        if nvalue != value:
            report('address %d, wrote %d, returned %d'
                   % (offset, value, nvalue))
        return nvalue

class IntegerRegister(object):
    def __init__(self, link, offset):
        self.link = link
        self.offset = long(offset)

    def read(self):
        return self.link.read(self.offset)

    def write(self, value):
        return self.link.write(self.offset, value)

class ToggleRegister(object):
    def __init__(self, link, (offset, bit)):
        self.link = link
        self.offset = long(offset)
        self.bit = int(bit)
        self.mask = int(1) << int(bit)

    def read(self):
        word = int(self.link.read(self.offset))
        bit = (word >> self.bit) & int(1)
        return (bit != 0)

    def write(self, state):
        word = int(self.link.read(self.offset))
        word &= ~self.mask
        if state: word |= self.mask
        return self.link.write(self.offset, word)

class MultiIntegerRegister(object):
    def __init__(self, link, offsets, eachWidth):
        self.link = link
        self.offsets = map(long, offsets)
        self.eachWidth = long(eachWidth)
        self.mask = (1L << self.eachWidth) - 1L

    def read(self):
        value = 0L
        shift = 0L
        for offset in self.offsets:
            part = self.link.read(offset)

            if (part & self.mask) != part:
                report('address %ld has value %ld too large for %ld bits'
                       % (offset, part, self.eachWidth))

            part <<= shift
            shift += self.eachWidth
            value |= part
        return value

    def write(self, value):
        nvalue = long(value)
        for offset in self.offsets:
            part = nvalue & self.mask
            nvalue >>= self.eachWidth
            self.link.write(offset, part)
        assert nvalue == 0
        nvalue = self.read()
        if nvalue != value:
            report('addresses [%s], wrote %ld, returned %ld'
                   % (', '.join(map(str, self.offsets)), value, nvalue))
        return nvalue

class FloatRegister(object): # 32-bits, taking up two full addresses
    def __init__(self, link, offset):
        self.link = link
        self.offset = long(offset)

    def read(self):
        # Read individual 16 bit unsigned integers
        lo = self.link.read(self.offset + 0)
        hi = self.link.read(self.offset + 1)
        # Pack into bytes as 2 x 16 bit unsigned integers
        data = struct.pack('>HH', lo, hi)
        # Unpack from bytes as 1 x 32 bit float
        return struct.unpack('>f', data)[0]

    def write(self, value):
        # Pack into bytes as 1 x 32 bit float
        data = struct.pack('>f', value)
        # Unpack from bytes as 2 x 16 bit unsigned integers
        lo, hi = struct.unpack('>HH', data)
        # Write individual 16 bit unsigned integers
        self.link.write(self.offset + 0, lo)
        self.link.write(self.offset + 1, hi)
        # Verify written value
        nvalue = self.read()
        if nvalue != value:
            report('address %ld float, wrote %f, returned %f'
                   % (self.offset, value, nvalue))
        return nvalue
