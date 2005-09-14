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

        # Place the widgets using layouts and yada, yada, yada...
        self.__setUpWidgets()

        self.connect(self.forwardButton, PYSIGNAL("clicked"),
                     self.slotNextScreen)
        self.connect(self.backButton, PYSIGNAL("clicked"),
                     self.slotPrevScreen)

    ##
    # set up the main window layout...
    def __setUpWidgets(self):
#        l = self.layout()

        main = QVBoxLayout(self)
        main.setSpacing(10)
        main.setMargin(20)

        top = QHBoxLayout()
#        top.setSpacing(10)
        top.addWidget(self.labelWidget)
        top.addStretch(1)
        top.addWidget(self.stageWidget)

        center = QHBoxLayout()
        center.setSpacing(20)
        center.addWidget(self.contentWidget)
        
        centerRight = QVBoxLayout()
        centerRight.setSpacing(10)
        centerRight.addWidget(self.helpWidget)

        buttons = QHBoxLayout()
        buttons.setSpacing(20)
        buttons.addWidget(self.backButton)
        buttons.addWidget(self.forwardButton)
        
        centerRight.addStretch(1)
        centerRight.addLayout(buttons)
        center.addLayout(centerRight)

        main.addLayout(top)
        main.addLayout(center)


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
        self.contentWidget.addScreen(stage, num, widget)

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
