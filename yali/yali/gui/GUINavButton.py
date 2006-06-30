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
    b = YaliButton(parent)
    b.setIcon(icon)
    return b

def nextButton(parent):
    return __button(parent, "button_forward")

def prevButton(parent):
    return __button(parent, "button_back")



class YaliButton(QWidget):

    def __init__(self, *args):
        apply(QWidget.__init__, (self,) + args)
    
        self.setCursor(QCursor(13))

        self.setFocusPolicy(self.TabFocus)

        self._pix = None
        self._pix_over = None
        self._pix_pressed = None
        self._pix_disabled = None
        self._enabled = True
        self._over = False
        self._text = None

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

        try:
            self._pix_disabled = ifactory.newPixmap("disabled_" + icon_name)
        except:
            # if disabled button is not present this means we don't need it!
            self._pix_disabled = ifactory.newPixmap(icon_name)

        self.setPixmap(self._pix)


    def setText(self, text):
        self._text = text

        self.setPaletteForegroundColor(ctx.consts.fg_color)
        f = self.font()
        f.setBold(True)
        self.setFont(f)


    def setPixmap(self, pix):
        self.setPaletteBackgroundPixmap(pix)


    def paintEvent(self, e):
        QWidget.paintEvent(self, e)
        if self._text:
            self.drawText(10, 18, self._text)


    def setEnabled(self, b = True):
        self._enabled = b

        # our signals are a bit lazy so trigger this a bit late...
        # bug #1548
        QTimer.singleShot(50, self.updateUi)

    def updateUi(self):
        if self._enabled:
            self.setCursor(QCursor(13))
            if self._over:
                self.setPixmap(self._pix_over)
            else:
                self.setPixmap(self._pix)
        else:
            self.setCursor(QCursor(0))
            self.setPixmap(self._pix_disabled)

    def mouseReleaseEvent(self, e):
        if self._enabled:
            self.emit(PYSIGNAL("signalClicked"), ())
            self.setPixmap(self._pix_over)
        else:
            self.setPixmap(self._pix_disabled)

    def mousePressEvent(self, e):
        if self._enabled:
            self.setPixmap(self._pix_pressed)
        else:
            self.setPixmap(self._pix_disabled)

    def enterEvent(self, e):
        self._over = True
        if self._enabled:
            self.setPixmap(self._pix_over)
        else:
            self.setPixmap(self._pix_disabled)

    def leaveEvent(self, e):
        self._over = False
        if self._enabled:
            self.setPixmap(self._pix)
        else:
            self.setPixmap(self._pix_disabled)


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
