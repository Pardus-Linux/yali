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
# ContentStack widget
class Widget(QWidgetStack):

    def __init__(self, *args):
        apply(QWidgetStack.__init__, (self,) + args)

        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding,
                                       QSizePolicy.Expanding))

        self.setFrameStyle(self.WinPanel | self.Plain)

        self.connect(ctx.screens, PYSIGNAL("signalAddScreen"),
                     self.slotAddScreen)

        self.connect(ctx.screens, PYSIGNAL("signalCurrent"),
                     self.slotScreenChanged)

        self.setPaletteBackgroundColor(QColor(255,255,255))

    ##
    # add a new screen.
    # @param obj(QObject): object that emits the signal.
    # @param w(QWidget): screen widget
    def slotAddScreen(self, obj, w ):
        self.addWidget(w)


    def slotScreenChanged(self, obj, index):
        scr = index - 1
        self.raiseWidget(scr)

        # FIXME: save the old screen's data in SystemConfiguration
