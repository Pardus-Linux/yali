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



##
# Stages of installation. Uses Steps with delegation.
class Stages:

    def __init__(self):
        self._steps = Steps()

    ##
    # add new a stage
    # @param index(int): index number.
    # @param name(string): stage name.
    def addStage(self, index, name):
        self._steps.addStep(index, name)

    ##
    # Sets the current stage and logs.
    # @param index(int): stage index to be the current.
    def setCurrent(self, index):
        self._steps.setCurrent(index)
        # We definetely need a logger :)
        #yali.logger.log("Changed stage to %s." % self._steps.getCurrent())



##
# Screens... Uses Steps with delegation as well.
class Screens:

    def __init__(self):
        self._steps = Steps()

    ##
    # add new a screen
    # @param index(int): index number.
    # @param data(ANY): screen data. Can be a QWidget for GUI implementation.
    def addScreen(self, index, data):
        self._steps.addStep(index, data)

    ##
    # Sets the current screen and logs.
    # @param index(int): screen index to be the current.
    def setCurrent(self, index):
        self._steps.setCurrent(index)
        # FIXME: is it feasible to write the widget object in GUI mode???
        #yali.logger.log("Changed screen to %s." % self._steps.getCurrent())
