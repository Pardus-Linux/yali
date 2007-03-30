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
        
        self.layout = QHBoxLayout(self)

        self.labelPix = QLabel(self)
        self.layout.addWidget(self.labelPix)

        self.labelText = QLabel(self)
        self.layout.addWidget(self.labelText)
        
        self._enabled = True
        self._toggled = False
        
    def setToggled(self,state):
        self._toggled = state
        self.toggle()

    def toggle(self):
        if self._toggled:
            self.labelPix.setMask(self.pix_toggled_mask)
            self.labelPix.setPixmap(self.pix_toggled)
        else:
            self.labelPix.setMask(self.pix_mask)
            self.labelPix.setPixmap(self.pix)

    def setIcon(self, icon_name):
        ifactory = ctx.iconfactory
        self.pix = ifactory.newPixmap(icon_name)
        self.pix_mask = self.pix.mask()
        self.pix_toggled = ifactory.newPixmap("toggled_" + icon_name)
        self.pix_toggled_mask = self.pix_toggled.mask()
        
        # fixed size is O.K.
        self.labelPix.setFixedSize(self.pix.size())

        self.labelPix.setMask(self.pix_mask)
        self.labelPix.setPixmap(self.pix)

    def setText(self, text):
        self.labelText.setText(text)
        self.setPaletteForegroundColor(ctx.consts.fg_color)
        f = self.font()
        self.labelText.setFont(f)

    def paintEvent(self, e):
        QWidget.paintEvent(self, e)

    def setEnabled(self, b = True):
        self._enabled = b
        # our signals are a bit lazy so trigger this a bit late...
        # bug #1548
        QTimer.singleShot(50, self.paintEvent)

    def mouseReleaseEvent(self, e):
        if self._enabled:
            self.emit(PYSIGNAL("signalClicked"), ())
            if self._toggled:
                self._toggled = False
                self.toggle()
            else:
                self._toggled = True
                self.toggle()
