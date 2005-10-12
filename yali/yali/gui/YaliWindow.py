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


from qt import *

import yali.gui.context as ctx

import GUITop
import GUIContentStack
import GUIHelp
import GUINavButton

##
# Widget for YaliWindow (you can call it MainWindow too ;).
class Widget(QMainWindow):

    def __init__(self, *args):
        apply(QMainWindow.__init__, (self,) + args)

        self.topWidget = GUITop.Widget(self)
        self.contentWidget = GUIContentStack.Widget(self)
        self.helpWidget = GUIHelp.Widget(self)
        self.forwardButton = GUINavButton.forwardButton(self)
        self.backButton = GUINavButton.backButton(self)

        # Place the widgets using layouts and yada, yada, yada...
        self.__setUpWidgets()

        self.connect(self.forwardButton, PYSIGNAL("signalClicked"),
                     self.slotNextScreen)
        self.connect(self.backButton, PYSIGNAL("signalClicked"),
                     self.slotPrevScreen)

        self.connect(self, PYSIGNAL("signalWindowSize"),
                     self.topWidget.slotResize)
        self.connect(self, PYSIGNAL("signalWindowSize"),
                     self.helpWidget.slotResize)


        #TESTING:
        self.setPaletteBackgroundPixmap(QPixmap("pics/back_tile.png"))

    ##
    # set up the main window layout...
    def __setUpWidgets(self):
#        l = self.layout()

        main = QVBoxLayout(self)
        main.setSpacing(0)
        main.setMargin(0)

        main.addWidget(self.topWidget)

        center = QHBoxLayout()
        center.setSpacing(20)
        center.setMargin(20)
        center.addWidget(self.contentWidget)
        
        centerRight = QVBoxLayout()
        centerRight.setSpacing(10)
        centerRight.setMargin(0)
        centerRight.addWidget(self.helpWidget)

        buttons = QHBoxLayout()
        buttons.setSpacing(20)
        buttons.addWidget(self.backButton)
        buttons.addWidget(self.forwardButton)
        
        centerRight.addStretch(1)
        centerRight.addLayout(buttons)
        center.addLayout(centerRight)

        main.addLayout(center)


    ##
    # Go to the next screen.
    def slotNextScreen(self):
        ctx.screens.next()

#FIXME: do this in GUIHelp connecting the screens.signalCurrent
#        self.helpWidget.showHelp(screen)


    ##
    # Go to the previous screen.
    def slotPrevScreen(self):
        ctx.screens.previous()


    ##
    # resizeEvent notifies others..
    # @param e(QResizeEvent): Qt resize event
    def resizeEvent(self, e):
        self.emit(PYSIGNAL("signalWindowSize"), (self, e.size()))
