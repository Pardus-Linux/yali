
from qt import *

from yali.steps import Steps

##
# Screens...
class Screens(QObject, Steps):

    def __init__(self, *args):
        Steps.__init__(self)
        apply(QObject.__init__, (self,) + args)

    ##
    # add new a screen
    # @param stage(int): stage number that the screen belongs to.
    # @param index(int): index number.
    # @param widget(QWidget): screen data. Can be a QWidget for GUI implementation.
    def addScreen(self, index, stage, widget):
        data = ScreenData(stage, widget)
        self.addStep(index, data)
        self.emit(PYSIGNAL("signalAddScreen"), (self, widget))


    def next(self):
        nxt = self.getCurrentIndex() + 1
        if self.hasIndex(nxt):
            self.__setCurrent(nxt)

    def previous(self):
        prev = self.getCurrentIndex() - 1
        if self.hasIndex(prev):
            self.__setCurrent(prev)
        

    ##
    # Sets the current screen and logs.
    # @param index(int): screen index to be the current.
    def __setCurrent(self, index):
        Steps.setCurrent(self, index)
        self.emit(PYSIGNAL("signalCurrent"), (self, index))

        # FIXME: is it feasible to write the widget object in GUI mode???
        #yali.logger.log("Changed screen to %s." % self._steps.getCurrent())


        

class ScreenData:
    _stage = None
    _widget = None
    #_text = None

    def __init__(self, stage, widget):
        self._stage = stage
        self._widget = widget

    def getWidget(self):
        return self._widget

    def getStage(self):
        return self._stage
