################################################################################
#                                                                              #
# Copyright (C) 2011-2015, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################

import sys
sys.path.append('..')

import os
import time
import unittest

from armoryengine.ALL import *



class TimerTest(unittest.TestCase):
    TIMER_CSV = 'timer.csv'

    def setUp(self):
        useMainnet()
        removeIfExists(self.TIMER_CSV)

    def tearDown(self):
        removeIfExists(self.TIMER_CSV)

    def testTimer(self):
        t = Timer()
        toSleep = 0.1
        t.startTimer('test')
        time.sleep(toSleep)
        self.assertRaises(TimerError, t.stopTimer, 'blah')
        t.stopTimer('test')
        result = t.readTimer('test')
        self.assertRaises(TimerError, t.readTimer, 'blah')
        self.assertTrue(result >= toSleep)
        t.printTimings()
        t.saveTimingsCSV(self.TIMER_CSV)
        text = open(self.TIMER_CSV).read()
        self.assertTrue('test' in text)
        self.assertRaises(TimerError, t.stopTimer, 'test')
        t.resetTimer('test')
        self.assertTrue(t.readTimer('test') > 100)
        self.assertRaises(TimerError, t.resetTimer, 'blah')

    def testTimeFunction(self):

        toSleep = 0.1

        @TimeThisFunction
        def toTime():
            time.sleep(toSleep)

        toTime()
        self.assertTrue(Timer().readTimer('toTime') > toSleep)
