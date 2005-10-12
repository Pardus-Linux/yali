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

        self.setSizePolicy( QSizePolicy(QSizePolicy.Minimum,
                                        QSizePolicy.Minimum))
        self.setFrameStyle(self.NoFrame)

        self.setPaletteBackgroundColor(QColor(255,203,3))

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

            if i == num:
                iterator.current().setPixmap(0, QPixmap("pics/active_bullet.png"))
            else:
                iterator.current().setPixmap(0, QPixmap("pics/inactive_bullet.png"))

            iterator += 1
            current = iterator.current()


##
# Stage item
class StageItem(QListViewItem):

    def __init__(self, parent, text, *args):
        apply(QLabel.__init__, (self, parent, text) + args)
