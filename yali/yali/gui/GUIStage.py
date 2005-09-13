# -*- coding: utf-8 -*-

from qt import *

from yali.steps import Stages

##
# Stage widget
class Widget(QListView):

    _stages = None
    _color_current = "#000000"
    _color_inactive = "#999999"

    def __init__(self, *args):
        apply(QLabel.__init__, (self,) + args)

        self._stages = Stages()

# do we need to show stage number? Currently we don't
#        self.addColumn(QString.null) # stage num
        self.addColumn(QString.null) # stage name
        self.header().hide()


    ##
    # add a new stage
    # @param num(int): stage number
    # @param text(string): stage text
    def addStage(self, num, text):
        self._stages.addStage(num, text)
        # add a listview item...
        i = StageItem(self, num, text)
        


    ##
    # set the current stage
    # @param num(int): stage number to be the current.
    def setCurrent(self, num):
        if num = self._stages.getCurrentIndex():
            return

        self._stages.setCurrent(num)

        # FIXME: define a way to show the current stage.
        # An icon on the left or colorizing are both OK.
        pass

##
# Stage item
class StageItem(QListViewItem):

    _num = None

    def __init__(self, parent, num, text, *args):
        apply(QLabel.__init__, (self, parent, text) + args)

        self._num = num
    
    ##
    # get the stage number
    def getNumber(self):
        return self._num
