# -*- coding: utf-8 -*-

from qt import *


##
# Help widget
class Widget(QTextView):

    def __init__(self, *args):
        apply(QTextView.__init__, (self,) + args)

        self.setSizePolicy( QSizePolicy(QSizePolicy.Preferred,
                                        QSizePolicy.Expanding))

        self.setFrameStyle(self.StyledPanel | self.Sunken)

        #TESTING:
        self.setFixedWidth(200)

    ##
    # Set help text from a file
    # @param help_file (string) file containing the help text.
    def setHelpFile(self, help_file):
        self.setText(open(help_file).read())
