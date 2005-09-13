# -*- coding: utf-8 -*-

# There are two different steps one must pass during the
# installation: stages and screens. User will only interact with
# screens and will see and and indicator showing the stages.
# Basicly installer will fulfill the process passing three main
# stages; 'preparation before install', 'system installation' and
# 'basic setup'. Each stage can have different number of screens
# though...


class Steps:

    def __init__(self):
        self._steps = {}
        self._current = None

    ##
    # Add a new step.
    # @param index(int): index number used for the ordering of steps.
    # @param step(ANY): step data.
    def addStep(self, index, step):
        
        if self._steps[index]:
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
