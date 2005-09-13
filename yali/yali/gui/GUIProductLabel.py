# -*- coding: utf-8 -*-

from qt import *


##
# ProductLabel widget
class Widget(QLabel):

    def __init__(self, *args):
        apply(QLabel.__init__, (self,) + args)

        # FIXME: We should use an image or so...

        # TESTING
        f = self.font()
        f.setBold(True)
        f.setPointSize(30)
        self.setFont(f)
        self.setText("Pardus 1.0")
        # END TEST
