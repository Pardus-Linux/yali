# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2007, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#


from os.path import join, exists
import locale
from qt import *

import yali.gui.context as ctx
import GUINavButton

##
# Help widget
class Widget(QWidget):

    def __init__(self, *args):
        apply(QWidget.__init__, (self,) + args)

        l = QVBoxLayout(self)
        l.setSpacing(10)

        self.tv = QTextView(self)

        self.tv.setSizePolicy( QSizePolicy(QSizePolicy.Preferred,
                                        QSizePolicy.Expanding))
        self.tv.setHScrollBarMode(QScrollView.AlwaysOff)
        self.tv.setVScrollBarMode(QScrollView.AlwaysOff)
        self.tv.setFrameStyle(self.tv.NoFrame)

        self.tv.setPaletteBackgroundColor(ctx.consts.bg_color)
        self.tv.setPaletteForegroundColor(ctx.consts.fg_color)


        up_layout = QHBoxLayout(l)
        self.up = GUINavButton.YaliButton(self)
        self.up.setIcon("help_button_up")
        up_layout.addStretch(1)
        up_layout.addWidget(self.up)
        up_layout.addStretch(1)

        l.addWidget(self.tv)

        down_layout = QHBoxLayout(l)
        self.down = GUINavButton.YaliButton(self)
        self.down.setIcon("help_button_down")
        down_layout.addStretch(1)
        down_layout.addWidget(self.down)
        down_layout.addStretch(1)


        self.connect(ctx.screens, PYSIGNAL("signalCurrent"),
                     self.slotScreenChanged)

        self.connect(self.up, PYSIGNAL("signalClicked"),
                     self.slotUP)
        self.connect(self.down, PYSIGNAL("signalClicked"),
                     self.slotDOWN)


    ##
    # Screen is changed, show the corresponding help text
    def slotScreenChanged(self):
        self.tv.setText(ctx.screens.getCurrent().getWidget().help)

        # show at start
        self.tv.moveCursor(self.tv.MoveHome, False)
        self.tv.ensureCursorVisible()

    ##
    # resize the widget
    def slotResize(self, obj, size):
        w = size.width()
        h = size.height()

        # calculate a proper size for the widget
        self.setFixedWidth(w/4)
        self.setFixedHeight(6 * (h/10))


    def slotUP(self):
        self.tv.moveCursor(self.tv.MovePgUp, False)
        self.tv.ensureCursorVisible()

    def slotDOWN(self):
        self.tv.moveCursor(self.tv.MovePgDown, False)
        self.tv.ensureCursorVisible()
