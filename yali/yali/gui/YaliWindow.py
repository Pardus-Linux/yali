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

from os.path import join
from qt import *

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext


import yali.gui.context as ctx

import GUITop
import GUIContentStack
import GUIHelp
import GUIBottom

##
# Widget for YaliWindow (you can call it MainWindow too ;).
class Widget(QMainWindow):

    def __init__(self, *args):
        apply(QMainWindow.__init__, (self,) + args)

        self.topWidget = GUITop.Widget(self)
        self.contentWidget = GUIContentStack.Widget(self)
        self.helpWidget = GUIHelp.Widget(self)
        self.bottomWidget = GUIBottom.Widget(self)


        # Place the widgets using layouts and yada, yada, yada...
        self.__setUpWidgets()


        self.connect(self, PYSIGNAL("signalWindowSize"),
                     self.topWidget.slotResize)
        self.connect(self, PYSIGNAL("signalWindowSize"),
                     self.helpWidget.slotResize)

        self.connect(ctx.screens, PYSIGNAL("nextButtonDisabled"),
                     self.slotNextDisabled)
        self.connect(ctx.screens, PYSIGNAL("prevButtonDisabled"),
                     self.slotPrevDisabled)
        self.connect(ctx.screens, PYSIGNAL("nextButtonEnabled"),
                     self.slotNextEnabled)
        self.connect(ctx.screens, PYSIGNAL("prevButtonEnabled"),
                     self.slotPrevEnabled)

        self.setPaletteBackgroundColor(ctx.consts.bg_color)
        self.setPaletteForegroundColor(ctx.consts.fg_color)

    ##
    # set up the main window layout...
    def __setUpWidgets(self):
#        l = self.layout()

        main = QVBoxLayout(self)

        main.addWidget(self.topWidget)

        center = QHBoxLayout()
        left_spacer = QSpacerItem(20,20, QSizePolicy.Fixed, QSizePolicy.Fixed)
        center.addItem(left_spacer)
        center.addWidget(self.contentWidget)
        center.addWidget(self.helpWidget)
        right_spacer = QSpacerItem(20,20, QSizePolicy.Fixed, QSizePolicy.Fixed)
        center.addItem(right_spacer)

        main.addLayout(center)
        main.addWidget(self.bottomWidget)


    # Enable/Disable buttons

    def slotNextDisabled(self):
        self.bottomWidget.nextButton.setEnabled(False)

    def slotPrevDisabled(self):
        self.bottomWidget.prevButton.setEnabled(False)

    def slotNextEnabled(self):
        self.bottomWidget.nextButton.setEnabled(True)

    def slotPrevEnabled(self):
        self.bottomWidget.prevButton.setEnabled(True)


    ##
    # resizeEvent notifies others..
    # @param e(QResizeEvent): Qt resize event
    def resizeEvent(self, e):
        self.emit(PYSIGNAL("signalWindowSize"), (self, e.size()))


    count = 0
    def mousePressEvent(self, e):
        if not e.globalX() and not e.globalY():
            OiEvent(self)
            self.count += 1
            if self.count > 10:
                OiEvent2(self)
                self.count = 0


class OiEvent(QMainWindow):
    def __init__(self, parent):
        self.pix = ctx.iconfactory.newPixmap("oi")
        self.w = self.pix.width()
        self.h = self.pix.height()
        QMainWindow.__init__(self, parent, "ewin1", Qt.WStyle_NoBorder)
        self.setFixedSize(self.w, self.h)
        self.top_x = parent.width() - self.w
        self.top_y = parent.height() - self.h
        self.setPaletteBackgroundPixmap(self.pix)
        self.setMask(self.pix.mask())
        self.x = self.top_x
        self.y = parent.height()
        self.move(self.x, self.y)
        self.timer = QTimer(self)
        self.connect(self.timer, SIGNAL("timeout()"), self.slotTimeTick)
        self.timer.start(50, False)
        self.dir = 0
        self.accel = 20
        self.show()
    
    def slotTimeTick(self):
        if self.dir == 0:
            self.y -= self.accel
            if self.y < self.top_y:
                self.dir = 1
                self.count = 0
                self.y = self.top_y
            if self.accel > 1:
                self.accel -= 1
        elif self.dir == 1:
            self.count += 1
            if self.count > 15:
                self.dir = 2
        elif self.dir == 2:
            self.x += self.accel
            if self.x >= self.top_x + self.pix.width():
                self.timer.stop()
                self.close(True)
                return
            if self.accel < 6:
                self.accel += 1
        self.move(self.x, self.y)


class OiEvent2(QMainWindow):
    def __init__(self, parent):
        self.pix = ctx.iconfactory.newPixmap("oi2")
        self.w = self.pix.width()
        self.h = self.pix.height()
        QMainWindow.__init__(self, parent, "ewin2", Qt.WStyle_NoBorder)
        self.setFixedSize(self.w, self.h)
        self.end = parent.width() + self.w
        self.x = 0 - self.w
        self.y = (parent.height() - self.h)/2
        self.setPaletteBackgroundPixmap(self.pix)
        self.setMask(self.pix.mask())
        self.move(self.x, self.y)
        self.timer = QTimer(self)
        self.connect(self.timer, SIGNAL("timeout()"), self.slotTimeTick)
        self.timer.start(50, False)
        self.first_y = self.y
        self.dir = 1
        self.show()
    
    def slotTimeTick(self):
        self.x += 2
        
        if self.x >= self.end:
            self.timer.stop()
            self.close(True)
            return


        dif = self.y - self.first_y
        if abs(dif) == 8 and self.dir:
            self.dir = 0
        elif dif >= 8:
            self.dir = -1
        elif dif <= -8:
            self.dir = 1

        if self.dir == 1:
            self.y += 1
        elif self.dir == -1:
            self.y -= 1
        
        self.move(self.x, self.y)


        print "lolo"
        print dif, self.dir

