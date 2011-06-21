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
        if not self.conn.connect():
            raise RuntimeError('Could not connect to host %s port %d' % (host, port))

    def read(self, offset):
        # Adjust offset due to weirdness.
        offset -= 40000

        # Create request.
        assert offset is not None
        assert offset >= 0
        req = ReadInputRegistersRequest(offset, 1)
        assert req is not None

        # Execute and return response.
        res = self.conn.execute(req)
        assert res is not None

        # Extract single value from response.
        values = res.registers
        assert values is not None
        assert len(values) == 1
        return long(values[0])

    def write(self, offset, value):
        # Adjust offset due to weirdness.
        offset -= 40000

        # Create request.
        assert offset is not None
        assert offset >= 0
        assert value is not None
        req = WriteSingleRegisterRequest(offset, value)

        # Execute and return response.
        res = self.conn.execute(req)
        assert res is not None
        assert res.value is not None
        nvalue = res.value
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
        state = (word >> self.bit) & int(1)
        return (state != 0)

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

class DwordRegister(object): # 32-bits, taking up two full addresses
    def __init__(self, link, offset):
        self.link = link
        self.offset = long(offset)

    def read(self):
        # Read individual 16 bit unsigned integers
        lo = self.link.read(self.offset + 0)
        hi = self.link.read(self.offset + 1)
        # Pack into bytes as 2 x 16 bit unsigned integers
        data = struct.pack('>HH', lo, hi)
        # Unpack from bytes as 1 x 32 bit integer
        return struct.unpack('>I', data)[0]

    def write(self, value):
        # Pack into bytes as 1 x 32 bit integer
        data = struct.pack('>I', value)
        # Unpack from bytes as 2 x 16 bit unsigned integers
        lo, hi = struct.unpack('>HH', data)
        # Write individual 16 bit unsigned integers
        self.link.write(self.offset + 0, lo)
        self.link.write(self.offset + 1, hi)
        # Verify written value
        nvalue = self.read()
        if nvalue != value:
            report('address %ld dword, wrote %ld, returned %ld'
                   % (self.offset, value, nvalue))
        return nvalue
