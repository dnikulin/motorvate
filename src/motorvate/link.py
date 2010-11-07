# Copyright (c) 2010 Dmitri Nikulin
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
        return self.conn.execute(req).value

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
        self.offset = offset

    def read(self):
        return self.link.read(self.offset)

    def write(self, value):
        return self.link.write(self.offset, value)

class MultiIntegerRegister(object):
    def __init__(self, link, offsets, eachWidth):
        self.link = link
        self.offsets = offsets
        self.eachWidth = long(eachWidth)
        self.mask = (1L << self.eachWidth) - 1

    def read(self):
        value = 0
        shift = 0
        for offset in self.offsets:
            part = self.link.read(offset)

            if (part & self.mask) != part:
                report('address %d has value %d too large for %d bits'
                       % (offset, part, self.eachWidth))

            part <<= shift
            shift += self.eachWidth
            value |= part
        return value

    def write(self, value):
        nvalue = value
        for offset in self.offsets:
            part = nvalue & self.mask
            nvalue >>= self.eachWidth
            self.link.write(offset, part)
        assert nvalue == 0
        nvalue = self.read()
        report('addresses [%s], wrote %d, returned %d'
               % (', '.join(self.offsets), value, nvalue))
        return nvalue
