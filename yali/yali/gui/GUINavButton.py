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

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext


import yali.gui.context as ctx


def __button(parent, icon):
    b = NavButton(parent)
    b.setIcon(icon)
    return b

def nextButton(parent):
    return __button(parent, "button_forward")

def prevButton(parent):
    return __button(parent, "button_back")



class NavButton(QWidget):

    def __init__(self, *args):
        apply(QWidget.__init__, (self,) + args)
    
        l = QVBoxLayout(self)
        self.label = QLabel(self)
        l.addWidget(self.label)

        self.setCursor(QCursor(13))

        self.setFocusPolicy(self.TabFocus)

        self._pix = None
        self._pix_over = None
        self._pix_pressed = None
        self._pix_disabled = None
        self._enabled = True

    def setIcon(self, icon_name):
        ifactory = ctx.iconfactory
        self._pix = ifactory.newPixmap(icon_name)

        # fixed size is O.K.
        self.setFixedSize(self._pix.size())


        # set a common mask for same sized images.
        bmap = self._pix.mask()
        self.setMask(bmap)

        self._pix_over = ifactory.newPixmap("over_" + icon_name)

        self._pix_pressed = ifactory.newPixmap("pressed_" + icon_name)

        self._pix_disabled = ifactory.newPixmap("disabled_" + icon_name)

        self.label.setPixmap(self._pix)

    def setEnabled(self, b = True):
        self._enabled = b

        if self._enabled:
            self.label.setPixmap(self._pix)
            self.setCursor(QCursor(13))
        else:
            self.label.setPixmap(self._pix_disabled)
            self.setCursor(QCursor(0))
            

    def mouseReleaseEvent(self, e):
        if self._enabled:
            self.emit(PYSIGNAL("signalClicked"), ())
            self.label.setPixmap(self._pix_over)
        else:
            self.label.setPixmap(self._pix_disabled)

    def mousePressEvent(self, e):
        if self._enabled:
            self.label.setPixmap(self._pix_pressed)
        else:
            self.label.setPixmap(self._pix_disabled)

    def enterEvent(self, e):
        if self._enabled:
            self.label.setPixmap(self._pix_over)
        else:
            self.label.setPixmap(self._pix_disabled)

    def leaveEvent(self, e):
        if self._enabled:
            self.label.setPixmap(self._pix)
        else:
            self.label.setPixmap(self._pix_disabled)


    # handle keyboard focus/press events

    def focusInEvent(self, e):
        self.enterEvent(e)

    def focusOutEvent(self, e):
        self.leaveEvent(e)

    def keyPressEvent(self, e):
        if e.key() == self.Key_Return or e.key() == self.Key_Space:
            self.mousePressEvent(e)

    def keyReleaseEvent(self, e):
        if e.key() == self.Key_Return or e.key() == self.Key_Space:
            self.mouseReleaseEvent(e)
