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

from os.path import exists, join
from qt import *

from yali.gui.GUIException import GUIError

class IconError(GUIError):
    pass


class IconFactory:

    def __init__(self, base_dir):
        self._dir = base_dir
        self._icon_name = None

    def __icon_path(self):

        p = join(self._dir, self._icon_name)
        p += ".png"
        if exists(p):
            return p
        else:
            raise IconError, "icon not found: %s" % (p)

    def newImage(self, name):
        self._icon_name = name
        return QImage(self.__icon_path())

    def newPixmap(self, name):
        self._icon_name = name
        return QPixmap(self.__icon_path())
