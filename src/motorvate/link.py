# Copyright (c) 2010 Dmitri Nikulin
# See LICENSE-MIT for details
# Part of the motorvation project

from pymodbus.client.sync import ModbusTcpClient
from pymodbus.constants import Defaults

from pymodbus.register_read_message import ReadInputRegistersRequest
from pymodbus.register_write_message import WriteSingleRegisterRequest

class ControlLink(object):
    def __init__(self, host, port=Defaults.Port):
        self.conn = ModbusTcpClient(host, port)
        self.conn.connect()

    def write(self, offset, value):
        req = WriteSingleRegisterRequest(offset, value)
        return self.conn.execute(req).value

    def read(self, offset):
        req = ReadInputRegistersRequest(offset)
        return self.conn.execute(req).value
