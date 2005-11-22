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

from os.path import join
from qt import *

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext


import yali.gui.context as ctx
from yali.gui.YaliDialog import Dialog

import GUITop
import GUIContentStack
import GUIHelp
import GUINavButton
import GUIRelNotes

##
# Widget for YaliWindow (you can call it MainWindow too ;).
class Widget(QMainWindow):

    def __init__(self, *args):
        apply(QMainWindow.__init__, (self,) + args)

        self.topWidget = GUITop.Widget(self)
        self.contentWidget = GUIContentStack.Widget(self)
        self.helpWidget = GUIHelp.Widget(self)
        self.nextButton = GUINavButton.nextButton(self)
        self.prevButton = GUINavButton.prevButton(self)
        self.relNotes = QPushButton(_("Release Notes"), self)

        # Place the widgets using layouts and yada, yada, yada...
        self.__setUpWidgets()

        self.connect(self.nextButton, PYSIGNAL("signalClicked"),
                     self.slotNextScreen)
        self.connect(self.prevButton, PYSIGNAL("signalClicked"),
                     self.slotPrevScreen)

        self.connect(self, PYSIGNAL("signalWindowSize"),
                     self.topWidget.slotResize)
        self.connect(self, PYSIGNAL("signalWindowSize"),
                     self.helpWidget.slotResize)

        self.connect(ctx.screens, PYSIGNAL("nextButtonDisabled"),
                     self.slotNextDisabled)
        self.connect(ctx.screens, PYSIGNAL("prevButtonDisabled"),
                     self.slotPrevDisabled)
        self.connect(ctx.screens, PYSIGNAL("nextButtonEnabled"),
                     self.slotNextEnabled)
        self.connect(ctx.screens, PYSIGNAL("prevButtonEnabled"),
                     self.slotPrevEnabled)


        self.connect(self.relNotes, SIGNAL("clicked()"),
                     self.showReleaseNotes)


        self.setPaletteBackgroundPixmap(ctx.iconfactory.newPixmap("back_tile"))

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

        centerRight.addWidget(self.relNotes)

        buttons = QHBoxLayout()
        buttons.setSpacing(20)
        buttons.addWidget(self.prevButton)
        buttons.addWidget(self.nextButton)
        
        centerRight.addStretch(1)
        centerRight.addLayout(buttons)
        center.addLayout(centerRight)

        main.addLayout(center)


    ##
    # Go to the next screen.
    def slotNextScreen(self):
        ctx.screens.next()

    ##
    # Go to the previous screen.
    def slotPrevScreen(self):
        ctx.screens.previous()


    # Enable/Disable buttons

    def slotNextDisabled(self):
        self.nextButton.setEnabled(False)

    def slotPrevDisabled(self):
        self.prevButton.setEnabled(False)

    def slotNextEnabled(self):
        self.nextButton.setEnabled(True)

    def slotPrevEnabled(self):
        self.prevButton.setEnabled(True)


    def showReleaseNotes(self):
        # make a release notes dialog
        r = GUIRelNotes.Widget(self)
        d = Dialog(_("Release Notes"), r, self)
        d.resize(500,400)
        d.exec_loop()


    ##
    # resizeEvent notifies others..
    # @param e(QResizeEvent): Qt resize event
    def resizeEvent(self, e):
        self.emit(PYSIGNAL("signalWindowSize"), (self, e.size()))
