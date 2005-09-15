# -*- coding: utf-8 -*-

from qt import *

import yali.gui.context as ctx

##
# Help widget
class Widget(QTextView):

    def __init__(self, *args):
        apply(QTextView.__init__, (self,) + args)

        self.setSizePolicy( QSizePolicy(QSizePolicy.Preferred,
                                        QSizePolicy.Expanding))

        self.setFrameStyle(self.WinPanel | self.Plain)

        self.connect(ctx.screens, PYSIGNAL("signalCurrent"),
                     self.slotScreenChanged)

        self.setHelpFile(1)

    ##
    # Set help text from a file
    # @param help_file (string) file containing the help text.
    def setHelpFile(self, file_index):

        # TODO: Do not forget localization!
        help_file = "yali/gui/screen_help/" + str(file_index) + ".html"
        self.setText(open(help_file).read())

    ##
    # Screen is changed, show the corresponding help file
    def slotScreenChanged(self, obj, index):
        self.setHelpFile(index)

    ##
    # resize the widget
    def slotResize(self, obj, size):
        w = size.width()
        h = size.height()

        # FIXME:  calculate a proper size for the widget
        self.setFixedWidth(w/4)
        self.setFixedHeight(4 * (h/7))
