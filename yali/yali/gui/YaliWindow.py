# -*- coding: utf-8 -*-

from qt import *

import GUIProductLabel
import GUIStage
import GUIContentStack
import GUIHelp
import GUINavButton

##
# Widget for YaliWindow (you can call it MainWindow too ;).
class Widget(QMainWindow):

    def __init__(self, *args):
        apply(QMainWindow.__init__, (self,) + args)

        self.labelWidget = GUIProductLabel.Widget(self)
        self.stageWidget = GUIStage.Widget(self)
        self.contentWidget = GUIContentStack.Widget(self)
        self.helpWidget = GUIHelp.Widget(self)
        self.forwardButton = GUINavButton.forwardButton(self)
        self.backButton = GUINavButton.backButton(self)

        # Place the widgets using layouts and so, handle other events
        # and yada, yada, yada...

        self.connect(self.forwardButton, PYSIGNAL("clicked"),
                     self.slotNextScreen)
        self.connect(self.backButton, PYSIGNAL("clicked"),
                     self.slotPrevScreen)

    ##
    # Add a new stage. stageWidget will handle the inner details
    # (using yali.steps.Stages).
    # @param num(int): stage number
    # @param text(string): stage text
    def addStage(self, num, text):
        self.stageWidget.addStage(num, text)

    ##
    # Add a new screen. contentWidget will handle the inner details
    # (using yali.steps.Screens).
    # @param stage(int): stage number that the screen blongs to.
    # @param num(int): screen number
    # @param widget(QWidget): screen widget.
    def addScreen(self, stage, num, widget):
        self.contentWidget(stage, num, widget)

    ##
    # Go to the next screen.
    def slotNextScreen(self):
        self.contentWidget.next()

        screen = self.contentWidget.currentScreen()
        self.helpWidget.showHelp(screen)

        stage = self.contentWidget.currentStage()
        self.stageWidget.setStage(stage)

    ##
    # Go to the previous screen.
    def slotPrevScreen(self):
        self.contentWidget.prev()

        screen = self.contentWidget.currentScreen()
        self.helpWidget.showHelp(screen)

        stage = self.contentWidget.currentStage()
        self.stageWidget.setStage(stage)
