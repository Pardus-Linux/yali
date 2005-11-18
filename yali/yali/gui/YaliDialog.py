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


class Title(QLabel):
    def __init__(self, *args):
        QLabel.__init__(self, *args)

        self.setAlignment(QLabel.AlignCenter)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Preferred,QSizePolicy.Maximum,0,0,self.sizePolicy().hasHeightForWidth()))
        self.setPaletteBackgroundColor(QColor(255,203,3))

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


class Dialog(QMainWindow):
    def __init__(self, t, w, parent):
        QMainWindow.__init__(self, parent)

        frame = QFrame(self)
        frame.setFrameStyle(frame.PopupPanel|frame.Plain)
        self.setCentralWidget(frame)
        layout = QGridLayout(frame, 1, 1, 1, 1)
        self.setMinimumSize(400, 300)
        w.reparent(frame, 0, QPoint(0,0), True)

        title = Title('<font size="+1"><b>%s</b></font>' % t, frame)
        layout.addWidget(title, 0, 0)
        layout.addWidget(w, 1, 0)
        

    

