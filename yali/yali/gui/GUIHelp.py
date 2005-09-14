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

    ##
    # Set help text from a file
    # @param help_file (string) file containing the help text.
    def setHelpFile(self, help_file):
        self.setText(open(help_file).read())

    ##
    # resize the widget
    def slotResize(self, obj, size):
        w = size.width()
        # FIXME:  calculate a proper size for widget width
        self.setFixedWidth(w/4)
