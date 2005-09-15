# -*- coding: utf-8 -*-

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

        #TESTING:
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
