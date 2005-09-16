# -*- coding: utf-8 -*-

from qt import *

from yali.gui.installwidget import InstallWidget

##
# Partitioning screen.
class Widget(InstallWidget):

    def __init__(self, *args):
        apply(InstallWidget.__init__, (self,) + args)
        
        pass

