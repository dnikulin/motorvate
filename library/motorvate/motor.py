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

from link import ToggleRegister, FloatRegister
from tools import report

from time import sleep

class Motor(object):
    def __init__(self, link, aSwitch, aHome, aHomed, aMove, aMoving, aPos):
        report("Motor(aSwitch=%s, aHome=%s, aHomed=%s, aMove=%s, aMoving=%s, aPos=%s)" %
               (repr(aSwitch), repr(aHome), repr(aHomed), repr(aMove), repr(aMoving), repr(aPos)))

        # Create registers for each control address.
        self.rSwitch = ToggleRegister(link, aSwitch)
        self.rHome   = ToggleRegister(link, aHome)
        self.rHomed = ToggleRegister(link, aHomed)
        self.rMove   = ToggleRegister(link, aMove)
        self.rMoving = ToggleRegister(link, aMoving)
        self.rPos    =  FloatRegister(link, aPos)

    # Homed logic.

    def home(self):
        report("Motor.home()")
        self.rSwitch.write(True)
        self.rHome.write(False)
        self.rMove.write(False)
        self.rHome.write(True)
        while not self.isHomed():
            sleep(0.1)
        self.rHome.write(False)

    def isHomed(self):
        homed = self.rHomed.read()
        report("Motor.isHomed() -> %s" % repr(homed))
        return homed

    # Moving logic.

    def move(self, position):
        report("Motor.move(%s)" % repr(position))
        self.rSwitch.write(True)
        self.rHome.write(False)
        self.rMove.write(False)
        self.rPos.write(float(position))
        self.rMove.write(True)
        while self.isMoving():
            sleep(0.1)
        self.rMove.write(False)

    def isMoving(self):
        moving = not self.rMoving.read()
        report("Motor.isMoving() -> %s" % repr(moving))
        return moving
