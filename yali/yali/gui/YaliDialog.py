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

from qt import *

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

import yali.gui.context as ctx

class Title(QLabel):
    def __init__(self, *args):
        QLabel.__init__(self, *args)

        self.setAlignment(QLabel.AlignCenter)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Preferred,QSizePolicy.Maximum,0,0,self.sizePolicy().hasHeightForWidth()))

        self.move = 0
        self.mainwidget = self.parent().parent()

    def mousePressEvent(self, event):
        self.move = 1
        self.start_x = event.globalPos().x()
        self.start_y = event.globalPos().y()
        wpos = self.mainwidget.mapToGlobal(QPoint(0,0))
        self.w_x = wpos.x()
        self.w_y = wpos.y()
    
    def mouseReleaseEvent(self, event):
        self.move = 0
    
    def mouseMoveEvent(self, event):
        if self.move:
            pos = event.globalPos()
            newpos = QPoint()
            newpos.setX(self.w_x + pos.x() - self.start_x)
            newpos.setY(self.w_y + pos.y() - self.start_y)
            self.mainwidget.move(newpos)

class Button(QLabel):
    def __init__(self,buttonImage, *args):
        QLabel.__init__(self, *args)
        self.pix = buttonImage
        self.setPixmap(ctx.iconfactory.newPixmap(buttonImage))
        self.setFixedWidth(18)

    def mousePressEvent(self, e):
        self.emit(PYSIGNAL("signalClicked"), ())

    def toggleImage(self,alternateButtonImage=None):
        if alternateButtonImage:
            img = alternateButtonImage
        else:
            img = self.pix
        self.setPixmap(ctx.iconfactory.newPixmap(img))

class Dialog(QDialog):
    def __init__(self, t, w, parent,extraButtons = False):
        QDialog.__init__(self, parent)
        
        self.minimized = False
        self.firstHeight = self.height()
        
        l = QHBoxLayout(self)
        frame = QFrame(self)
        frame.setMinimumHeight(20)
        frame.setPaletteBackgroundColor(ctx.consts.border_color)
        frame.setFrameStyle(frame.PopupPanel|frame.Plain)
        l.addWidget(frame)
        
        layout = QGridLayout(frame, 1, 1, 1, 1)
        layout.setMargin(2)
        
        w.reparent(frame, 0, QPoint(0,0), True)
        w.setPaletteBackgroundColor(ctx.consts.bg_color)
        w.setPaletteForegroundColor(ctx.consts.fg_color)

        hbox = QHBoxLayout(frame)
        title = Title('<font size="+1"><b>%s</b></font>' % t, frame)
        close = Button("cross",frame)
        
        hbox.addWidget(title)
        
        if extraButtons:
            minimize = Button("minimize",frame)
            hbox.addWidget(minimize)
            self.connect(minimize, PYSIGNAL("signalClicked"),
                         self.doMinimize)
        hbox.addWidget(close)

        layout.addLayout(hbox, 0, 0)
        layout.addWidget(w, 1, 0)

        self.connect(close, PYSIGNAL("signalClicked"),
                     self.reject)
        
        
    def doMinimize(self):
        if self.minimized:
            self.resize(self.width(),self.firstHeight)
            self.sender().toggleImage()
            self.minimized=False
        else:
            self.resize(self.width(),0)
            self.sender().toggleImage("minimized")
            self.minimized=True

class WarningDialog(Dialog):

    def __init__(self, w, parent):
        self.warning_widget = w
        Dialog.__init__(self, _("Warning"), self.warning_widget, parent)

        self.connect(self.warning_widget, PYSIGNAL("signalOK"),
                     self.slotOK)
        self.connect(self.warning_widget, PYSIGNAL("signalCancel"),
                     self.slotCancel)

    def slotOK(self):
        self.done(1)

    def slotCancel(self):
        self.done(0)
