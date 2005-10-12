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

def forwardButton(parent):
    w = NavButton(parent)
    w.setIcon("button_forward.png")
    return w

def backButton(parent):
    w = NavButton(parent)
    w.setIcon("button_back.png")
    return w


class NavButton(QWidget):

    _pix = None
    _pix_over = None
    _pix_pressed = None

    def __init__(self, *args):
        apply(QWidget.__init__, (self,) + args)
    
        l = QVBoxLayout(self)
        self.label = QLabel(self)
        l.addWidget(self.label)

        self.setCursor(QCursor(13))

        # FIXME:
        # build the widget layout... or should be use QPushButton?
        # don't use fixed sizes
        # find a way to paint button background.
        self.setFixedSize(64, 64)

    def setIcon(self, icon_name):
        # FIXME: don't hard-code paths!!!
        icon_path = "pics/" + icon_name
        self._pix = QPixmap(icon_path)

        # set a common mask for same sized images.
        bmap = self._pix.mask()
        self.setMask(bmap)

        icon_path = "pics/" + "over_" + icon_name
        self._pix_over = QPixmap(icon_path)

        icon_path = "pics/" + "pressed_" + icon_name
        self._pix_pressed = QPixmap(icon_path)

        self.label.setPixmap(self._pix)

    def mouseReleaseEvent(self, e):
        self.emit(PYSIGNAL("signalClicked"), ())
        self.label.setPixmap(self._pix_over)

    def mousePressEvent(self, e):
        self.label.setPixmap(self._pix_pressed)

    def enterEvent(self, e):
        self.label.setPixmap(self._pix_over)

    def leaveEvent(self, e):
        self.label.setPixmap(self._pix)
