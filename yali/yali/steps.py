# -*- coding: utf-8 -*-
#
# Copyright (C) 2005, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#


# In GUI there are two different steps one must pass during the
# installation: stages and screens. User will only interact with
# screens and will see an indicator showing the stages. Basicly
# installer will fulfill the process passing three main stages;
# 'preparation before install', 'system installation' and 'basic
# setup'. Each stage can have different number of screens though...

from yali.exception import YaliError, YaliException

class Steps:

    def __init__(self):
        self._steps = {}
        self._current = None

    ##
    # Add a new step.
    # @param index(int): index number used for the ordering of steps.
    # @param step(ANY): step data.
    def addStep(self, index, step):

        if self._steps.has_key(index):
            e = "index %d is present." % index
            #should find a way to get debug status.
            #I know optparser is my friend :)
#            if DEBUG: e += "\nData: %s" % self._steps[index]
            raise YaliError, e

        self._steps[index] = step

        if not self._current:
            self.setCurrent(index)

    ##
    # Set the current step. This can be overriden by the implementors.
    # @param index(int): index of the step to be the current
    def setCurrent(self, index):
        self._current = index

    ##
    # Get current step data
    def getCurrent(self):
        return self._steps[self._current]

    ##
    # Get the current index number.
    def getCurrentIndex(self):
        return self._current

    ##
    # Get item by index number
    # @param num(int): index number
    def getItem(self, num):
        return self._steps[num]

    def getAllItems(self):
        return self._steps.values()

    def getAllIndexes(self):
        return self._steps.keys()

    def hasIndex(self, num):
        return self._steps.has_key(num)
