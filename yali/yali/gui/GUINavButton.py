# -*- coding: utf-8 -*-

from qt import *

def forwardButton(parent):
    w = NavButton(parent)
    w.setIcon("forward.png")
    return w

def backButton(parent):
    w = NavButton(parent)
    w.setIcon("back.png")
    return w


class Navbutton(QWidget):

    def __init__(self, *args):
        apply(QWidget.__init__, (self,) + args)

        # FIXME:
        # build the widget layout... or should be use QPushButton?

    def setIcon(self, icon_name):
        icon_path = "path/to/icons" + icon_name
        pix = QPixmap(icon_path)
        self._icon.setPixmap(pix)

    def mouseReleaseEvent(self, e):
        self.emit(PYSIGNAL("clicked"), ())
