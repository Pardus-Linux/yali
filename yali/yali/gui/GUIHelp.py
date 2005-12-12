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


from os.path import join, exists
import locale
from qt import *

import yali.gui.context as ctx

##
# Help widget
class Widget(QWidget):

    def __init__(self, *args):
        apply(QWidget.__init__, (self,) + args)

        l = QVBoxLayout(self)

        self.tv = QTextView(self)

        self.tv.setSizePolicy( QSizePolicy(QSizePolicy.Preferred,
                                        QSizePolicy.Expanding))
        self.tv.setHScrollBarMode(QScrollView.AlwaysOff)
        self.tv.setVScrollBarMode(QScrollView.AlwaysOff)
        self.tv.setFrameStyle(self.tv.NoFrame)

        self.tv.setPaletteBackgroundColor(ctx.consts.bg_color)
        self.tv.setPaletteForegroundColor(ctx.consts.fg_color)


        # up/down buttons
        self.up = QPushButton(self)
        self.up.setPixmap(ctx.iconfactory.newPixmap("scroll_up"))
        self.down = QPushButton(self)
        self.down.setPixmap(ctx.iconfactory.newPixmap("scroll_down"))

        l.addWidget(self.up)
        l.addWidget(self.tv)
        l.addWidget(self.down)

        self.connect(ctx.screens, PYSIGNAL("signalCurrent"),
                     self.slotScreenChanged)

        self.connect(self.up, SIGNAL("clicked()"),
                     self.slotUP)
        self.connect(self.down, SIGNAL("clicked()"),
                     self.slotDOWN)


    ##
    # Screen is changed, show the corresponding help text
    def slotScreenChanged(self):
        self.tv.setText(ctx.screens.getCurrent().getWidget().help)

    ##
    # resize the widget
    def slotResize(self, obj, size):
        w = size.width()
        h = size.height()

        # calculate a proper size for the widget
        self.setFixedWidth(w/4)
        self.setFixedHeight(4 * (h/7))


    def slotUP(self):
        self.tv.moveCursor(self.tv.MovePgUp, False)
        self.tv.ensureCursorVisible()

    def slotDOWN(self):
        self.tv.moveCursor(self.tv.MovePgDown, False)
        self.tv.ensureCursorVisible()
