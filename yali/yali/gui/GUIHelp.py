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


from os.path import join, exists
import locale
from qt import *

import yali.gui.context as ctx

##
# Help widget
class Widget(QTextView):

    def __init__(self, *args):
        apply(QTextView.__init__, (self,) + args)

        self.setSizePolicy( QSizePolicy(QSizePolicy.Preferred,
                                        QSizePolicy.Expanding))

        self.setFrameStyle(self.WinPanel | self.Plain)

        self.setPaletteBackgroundColor(QColor(204,204,204))

        self.connect(ctx.screens, PYSIGNAL("signalCurrent"),
                     self.slotScreenChanged)


    ##
    # Screen is changed, show the corresponding help text
    def slotScreenChanged(self):
        self.setText(ctx.screens.getCurrent().getWidget().help)

    ##
    # resize the widget
    def slotResize(self, obj, size):
        w = size.width()
        h = size.height()

        # calculate a proper size for the widget
        self.setFixedWidth(w/4)
        self.setFixedHeight(4 * (h/7))
