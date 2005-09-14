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

        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding,
                                       QSizePolicy.Expanding))

        self.setFrameStyle(self.StyledPanel | self.Sunken)

        #TESTING:
        self.setPaletteBackgroundColor(QColor(255,255,255))

    ##
    # add a new screen.
    # @param w(QWidget): screen widget
    def addScreen(self, stage, num, w):
        self.addWidget(w)

        # FIXME: provide a way to define stage. possibly in Screens...
        self._screens.addScreen(num, w)


    def currentScreen(self):
        return self._screens.getCurrentIndex()

    ##
    # go to the next screen.
    def next(self):
        pass

    ##
    # go to the previous screen.
    def prev(self):
        pass
