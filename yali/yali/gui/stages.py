
from qt import *

from yali.steps import Steps

##
# Stages of installation.
class Stages(QObject, Steps):

    def __init__(self, *args):
        Steps.__init__(self)
        apply(QObject.__init__, (self,) + args)

        

    ##
    # add new a stage
    # @param index(int): index number.
    # @param text(string): stage text
    def addStage(self, index, text):
        self.addStep(index, text)
        self.emit(PYSIGNAL("signalAddStage"), (self,
                                               "%d. %s" % (index, text)))

    ##
    # Sets the current stage and logs.
    # @param index(int): stage index to be the current.
    def setCurrent(self, index):
        Steps.setCurrent(self, index)
        self.emit(PYSIGNAL("signalCurrent"), (self, index))
        print "stages: current stage", index

        # We definetely need a logger :)
        #yali.logger.log("Changed stage to %s." % self._steps.getCurrent())


    def slotScreenChanged(self, obj, index):
        scrData = obj.getCurrent()
        curStage = scrData.getStage()

        if self.getCurrentIndex() == curStage or not self.hasIndex(curStage):
            return

        self.setCurrent(curStage)
        
