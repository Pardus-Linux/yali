# -*- coding: utf-8 -*-

from qt import *


##
# Help widget
class Widget(QTextView):

    def __init__(self, *args):
        apply(QTextView.__init__, (self,) + args)

        sp = QSizePolicy(QSizePolicy.Maximum,
                         QSizePolicy.Preferred)
        self.setSizePolicy(sp)

        self.setFrameStyle(self.NoFrame | self.Raised)

    ##
    # Set help text from a file
    # @param help_file (string) file containing the help text.
    def setHelpFile(self, help_file):
        self.setText(open(help_file).read())
