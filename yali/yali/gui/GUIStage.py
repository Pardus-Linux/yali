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
class Widget(QListView):

    _color_current = "#000000"
    _color_inactive = "#999999"

    def __init__(self, *args):
        apply(QListView.__init__, (self,) + args)

        self.addColumn(QString.null) # stage name
        self.header().hide()

        self.tw = self.width()
        self.th = self.height()
        self.tx = self.x()
        self.ty = self.y()
        self.fixBackground()

        self.setSizePolicy( QSizePolicy(QSizePolicy.Minimum,
                                        QSizePolicy.Minimum))
        self.setFrameStyle(self.NoFrame)

        self.setPaletteForegroundColor(ctx.consts.fg_color)

        f = self.font()
        f.setBold(True)
        self.setFont(f)

        self.setSelectionMode(self.NoSelection)
        self.setFocusPolicy(self.NoFocus)
        self.setVScrollBarMode(self.AlwaysOff)

        
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
        # add a listview item...
        i = StageItem(self, text)

        self.setColumnWidth( 0, self.columnWidth( 0 ) + 20 )

    ##
    # set the current stage. Iterate over the listview items and set
    # the icons.
    # @param obj(QObject): QObject that emits the signal.
    # @param num(int): stage number to be the current.
    def slotStageChanged(self, obj, num):

        iterator = QListViewItemIterator(self)
        current = iterator.current()
        i = 0
        while current:
            # stages start from 1 and ListViewItems start from 0. So
            # we increase 'i' at first.
            i += 1 

            ifactory = ctx.iconfactory
            if i == num:
                iterator.current().setPixmap(0, ifactory.newPixmap("active_bullet"))
            else:
                iterator.current().setPixmap(0, ifactory.newPixmap("inactive_bullet"))

            iterator += 1
            current = iterator.current()


##
# Stage item
class StageItem(QListViewItem):

    def __init__(self, parent, text, *args):
        apply(QLabel.__init__, (self, parent, text) + args)
