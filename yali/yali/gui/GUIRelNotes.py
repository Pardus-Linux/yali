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

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext


import yali.gui.context as ctx
from yali.gui.GUIException import *


##
# Help widget
class Widget(QTextView):

    def __init__(self, *args):
        apply(QTextView.__init__, (self,) + args)

        self.setSizePolicy( QSizePolicy(QSizePolicy.Preferred,
                                        QSizePolicy.Expanding))


        self.setPaletteBackgroundColor(ctx.consts.bg_color)

        # don't show links in diffrent color.
        self.setLinkUnderline(False)
        palette = self.palette()
        active_colors = palette.active()
        active_colors.setColor(active_colors.Link, ctx.consts.fg_color)
        palette.setActive(active_colors)
        self.setPalette(palette)

        rel_file = "releasenotes-" + ctx.consts.lang + ".html"
        rel_path = join(ctx.consts.source_dir, rel_file)

        if not exists(rel_path):
            raise GUIException, _("Can't open Release Notes file!")

        try:
            self.setText(codecs.open(rel_path, "r", "UTF-8").read())
        except Exception, e:
            raise GUIException, e
