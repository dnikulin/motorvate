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

from counters import Counters
from motor import Motor
from relay import Relay
from analog import Analog

# Base address for relays and counter control.
# XXX: This does not match Ken's PDF.
RC_BASE   = 42000

ANALOGS   = [42013, 42017, 42021, 42025]

MOTOR_YS  = (42002, 42037)
MOTOR_YA  = (42003, 42043)
MOTOR_ZS  = (42004, 42049)
MOTOR_TH1 = (42005, 42055)
MOTOR_TH2 = (42006, 42061)

MOTORS = [MOTOR_YS, MOTOR_YA, MOTOR_ZS, MOTOR_TH1, MOTOR_TH2]

COUNTER_TIMES  = [42073, 42075, 42077, 42079]
COUNTER_VALUES = [42029, 42031, 42033, 42035]

class World(object):
    def __init__(self, link):
        self.link = link

        self.relays = [Relay(link, (RC_BASE, bit)) for bit in range(0, 8)]

        self.analogs = [Analog(link, aValue) for aValue in ANALOGS]

        self.counters = Counters(link,
            (RC_BASE, 8), # 'Start' for all counters.
            [(RC_BASE, bit) for bit in range(9, 13)], # Stop for each counter.
            COUNTER_TIMES, # Time for each counter (two words).
            COUNTER_VALUES, # Value for each counter (two words).
        )

        self.motors = [
            Motor(
                link,
                (base, 0), # Enable.
                (base, 3), # Home.
                (base, 5), # Homing.
                (base, 1), # Move.
                (base, 4), # Moving.
                position   # Set position.
            )
            for (base, position) in MOTORS
        ]

        (self.ys, self.ya, self.zs, self.th1, self.th2) = self.motors
