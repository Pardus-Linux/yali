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

import yali.gui.context as ctx

##
# Stage widget
class Widget(QWidget):

    def __init__(self, *args):
        apply(QWidget.__init__, (self,) + args)

        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(20)
        self.stages = []

        self.tw = self.width()
        self.th = self.height()
        self.tx = self.x()
        self.ty = self.y()
        self.fixBackground()

        self.setSizePolicy( QSizePolicy(QSizePolicy.Minimum,
                                        QSizePolicy.Minimum))
        self.setPaletteForegroundColor(ctx.consts.fg_color)

        f = self.font()
        f.setBold(True)
        self.setFont(f)

        self.setFocusPolicy(self.NoFocus)


        self.connect(ctx.stages, PYSIGNAL("signalAddStage"),
                     self.slotAddStage)

        self.connect(ctx.stages, PYSIGNAL("signalCurrent"),
                     self.slotStageChanged)

    def fixBackground(self):
        self.pix = QPixmap(self.tw, self.th)
        self.pix.fill(self.parent(), self.tx, self.ty)
        self.setPaletteBackgroundPixmap(self.pix)

    def resizeEvent(self, event):
        self.tw = event.size().width()
        self.th = event.size().height()
        self.fixBackground()

    def moveEvent(self, event):
        self.tx = event.pos().x()
        self.ty = event.pos().y()
        self.fixBackground()

    ##
    # add a new stage
    # @param obj(QObject): QObject that emits the signal.
    # @param text(string): stage text
    def slotAddStage(self, obj, text):
        item = StageItem(self, text)
        self.stages.append(item)
        self.layout.addWidget(item)

    ##
    # set the current stage. Iterate over the listview items and set
    # the icons.
    # @param obj(QObject): QObject that emits the signal.
    # @param num(int): stage number to be the current.
    def slotStageChanged(self, obj, num):
        if not self.stages:
            return

        # Stages start from 1 and array items start from 0. So we
        # decrease 'num'.
        num -= 1

        # Deactivate all and activate the matched one. Dummy...
        for s in self.stages:
            s.setActive(False)
        self.stages[num].setActive(True)

##
# Stage item
class StageItem(QWidget):

    _color_active = "#000000"
    _color_inactive = "#999999"

    def __init__(self, parent, text, *args):
        apply(QWidget.__init__, (self, parent) + args)

        self.active = False
        self.text = text

        layout = QHBoxLayout(self)
        layout.addSpacing(5)
        self.icon = QLabel(self)
        layout.addWidget(self.icon)
        self.label = QLabel(self)
        layout.addWidget(self.label)

    def setActive(self, active=True):
        if active:
            self.icon.setPixmap(ctx.iconfactory.newPixmap("active_bullet"))
            self.label.setText("<font color=\"%s\">%s</font>" % (
                    self._color_active, self.text))
            self.label.setAlignment(QLabel.SingleLine)
        else:
            self.icon.setPixmap(ctx.iconfactory.newPixmap("inactive_bullet"))
            self.label.setText("<font color=\"%s\">%s</font>" % (
                    self._color_inactive, self.text))
            self.label.setAlignment(QLabel.SingleLine)
        self.active = active

        self.setFixedHeight(self.icon.height())
