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

from link import ToggleRegister, DwordRegister, FloatRegister
from tools import report

from time import time, sleep

class Counters(object):
    def __init__(self, link, aSwitch, aBusy, aTime, aValues):
        report("Counters(aSwitch=%s, aBusy=%s, aTime=%s, aValues=%s)" %
               (repr(aSwitch), repr(aBusy), repr(aTime), repr(aValues)))

        self.rSwitch = ToggleRegister(link, aSwitch)
        self.rBusy   = ToggleRegister(link, aBusy)
        self.rTime   =  FloatRegister(link, aTime)
        self.rValues = [DwordRegister(link, aValue) for aValue in aValues]

    def stop(self):
        report("Counters.stop()")
        self.rSwitch.write(False)

    def start(self):
        report("Counters.start()")
        self.rSwitch.write(True)

    def isBusy(self):
        done = self.rBusy.read()
        report("Counters.isBusy() -> %s" % repr(done))
        return done

    def setTime(self, time_ms):
        report("Counters.setTime(%s)" % repr(time_ms))
        self.rTime.write(float(int(time_ms)))

    def getCounts(self):
        counts = [rValue.read() for rValue in self.rValues]
        report("Counters.getCounts() -> %s" % repr(counts))
        return counts

    def measure(self, time_ms):
        report("Counters.measure(%s)" % repr(time_ms))

        # Stop counters if running.
        self.stop()

        # Specify time to count.
        self.setTime(time_ms)

        # Sample real time.
        t1 = time()

        # Start timer and counters.
        self.start()

        # Wait until time has elapsed.
        while self.isBusy():
            sleep(0.1)

        # Sample real time.
        t2 = time()

        # Calculate and report real time elapsed.
        taken_ms = int((t2 - t1) * 1000)
        report("Counters.measure(%s) took %d ms" % (repr(time_ms), taken_ms))

        # Read out counter values.
        counts = self.getCounts()

        # Stop counters.
        self.stop()
        self.setTime(0)
        return counts
