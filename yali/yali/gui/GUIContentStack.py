# -*- coding: utf-8 -*-

from qt import *

from yali.steps import Screens

##
# ContentStack widget
class Widget(QWidgetStack):

    _screens = None

    def __init__(self, *args):
        apply(QWidgetStack.__init__, (self,) + args)

        self._screens = Screens()

        self.setFrameStyle(self.StyledPanel | self.Sunken)

    ##
    # add a new screen.
    # @param w(QWidget): screen widget
    def addScreen(self, stage, num, w):
        self.addWidget(w)

        # FIXME: provide a way to define stage. possibly in Screens...
        self._screens.addScreen(num, w)

    ##
    # go to the next screen.
    def next(self):
        pass

    ##
    # go to the previous screen.
    def prev(self):
        pass
