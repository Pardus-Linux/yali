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

class YaliToggler(QWidget):

    def __init__(self, *args):
        apply(QWidget.__init__, (self,) + args)

        self.setFocusPolicy(self.TabFocus)

        self._pix = None
        self._pix_toggled = None
        self._enabled = True
        self._text = None
        self._toggled = False
        self.label = None
        
    def setToggled(self,state):
        self._toggled = state
        if self._toggled:
            self.setPixmap(self._pix_toggled)
        else:
            self.setPixmap(self._pix)

    def setIcon(self, icon_name):
        ifactory = ctx.iconfactory
        self._pix = ifactory.newPixmap(icon_name)

        # fixed size is O.K.
        self.setFixedSize(self._pix.size())

        # set a common mask for same sized images.
        bmap = self._pix.mask()
        self.setMask(bmap)

        self._pix_toggled = ifactory.newPixmap("toggled_" + icon_name)
        self.setPixmap(self._pix)

    def setText(self, text):
        self._text = text
        self.setPaletteForegroundColor(ctx.consts.fg_color)
        f = self.font()
        self.setFont(f)

    def setPixmap(self, pix):
        bmap = pix.mask()
        self.setMask(bmap)
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
        self.setPixmap(self._pix)

    def mouseReleaseEvent(self, e):
        if self._enabled:
            self.emit(PYSIGNAL("signalClicked"), ())
            if self._toggled:
                self._toggled = False
                self.setPixmap(self._pix)
            else:
                self._toggled = True
                self.setPixmap(self._pix_toggled)
