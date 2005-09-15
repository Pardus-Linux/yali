# -*- coding: utf-8 -*-

from qt import *


##
# Help widget
class Widget(QTextView):

    def __init__(self, *args):
        apply(QTextView.__init__, (self,) + args)

        self.setSizePolicy( QSizePolicy(QSizePolicy.Preferred,
                                        QSizePolicy.Expanding))

        self.setFrameStyle(self.WinPanel | self.Plain)

    ##
    # Set help text from a file
    # @param help_file (string) file containing the help text.
    def setHelpFile(self, help_file):
        self.setText(open(help_file).read())

    ##
    # resize the widget
    def slotResize(self, obj, size):
        w = size.width()
        h = size.height()

        # FIXME:  calculate a proper size for the widget
        self.setFixedWidth(w/4)
        self.setFixedHeight(4 * (h/7))
