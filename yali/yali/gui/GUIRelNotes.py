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
import codecs
from qt import *

import yali.gui.context as ctx

##
# Help widget
class Widget(QTextView):

    def __init__(self, *args):
        apply(QTextView.__init__, (self,) + args)

        self.setSizePolicy( QSizePolicy(QSizePolicy.Preferred,
                                        QSizePolicy.Expanding))

#        self.setFrameStyle(self.WinPanel | self.Plain)

        self.setPaletteBackgroundColor(QColor(204,204,204))

        rel_file = "releasenotes-" + ctx.consts.lang + ".html"
        rel_path = join(ctx.consts.source_dir, rel_file)
        self.setText(codecs.open(rel_path, "r", "UTF-8").read())
