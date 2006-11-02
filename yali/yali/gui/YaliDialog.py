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


class CloseButton(QLabel):
    def __init__(self, *args):
        QLabel.__init__(self, *args)

        self.setPixmap(ctx.iconfactory.newPixmap("cross"))
        self.setFixedWidth(18)

    def mousePressEvent(self, e):
        self.emit(PYSIGNAL("signalClicked"), ())


class Dialog(QDialog):
    def __init__(self, t, w, parent):
        QDialog.__init__(self, parent)

        l = QHBoxLayout(self)
        frame = QFrame(self)
        frame.setPaletteBackgroundColor(QColor(227,89,10))
        frame.setFrameStyle(frame.PopupPanel|frame.Plain)
        l.addWidget(frame)
        
        layout = QGridLayout(frame, 1, 1, 1, 1)
        layout.setMargin(4)
        w.reparent(frame, 0, QPoint(0,0), True)
        w.setPaletteBackgroundColor(ctx.consts.bg_color)
        w.setPaletteForegroundColor(ctx.consts.fg_color)

        hbox = QHBoxLayout(frame)
        title = Title('<font size="+1"><b>%s</b></font>' % t, frame)
        close = CloseButton(frame)
        hbox.addWidget(title)
        hbox.addWidget(close)

        layout.addLayout(hbox, 0, 0)
        layout.addWidget(w, 1, 0)

        self.connect(close, PYSIGNAL("signalClicked"),
                     self.reject)




    
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

