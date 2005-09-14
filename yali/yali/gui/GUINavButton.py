# -*- coding: utf-8 -*-

from qt import *

def forwardButton(parent):
    w = NavButton(parent)
    w.setIcon("button_forward.png")
    return w

def backButton(parent):
    w = NavButton(parent)
    w.setIcon("button_back.png")
    return w


class NavButton(QWidget):

    def __init__(self, *args):
        apply(QWidget.__init__, (self,) + args)
    
        l = QVBoxLayout(self)
        self.label = QLabel(self)
        l.addWidget(self.label)

        # FIXME:
        # build the widget layout... or should be use QPushButton?
        # don't use fixed sizes
        # find a way to paint button background.
        self.setFixedSize(64, 64)
        self.setPaletteBackgroundPixmap(QPixmap())

    def setIcon(self, icon_name):
        # FIXME: don't hard-code paths!!!
        icon_path = "pics/" + icon_name
        pix = QPixmap(icon_path)
        self.label.setPixmap(pix)

    def mouseReleaseEvent(self, e):
        self.emit(PYSIGNAL("clicked"), ())
