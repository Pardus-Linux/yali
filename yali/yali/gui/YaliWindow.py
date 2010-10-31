# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2010 TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#
import os
import sys
import codecs

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

from PyQt4 import QtGui
from PyQt4.QtCore import *
import QTermWidget
from pyaspects.weaver import *

import yali.util
import yali.sysutils
import yali.context as ctx
from yali.gui.Ui.main import Ui_YaliMain
from yali.gui.YaliDialog import Dialog, QuestionDialog
from yali.gui.YaliDialog import Tetris
from yali.gui.aspects import enableNavButtonsAspect, disableNavButtonsAspect, loggerAspect

##
# Widget for YaliWindow (you can call it MainWindow too ;).
class Widget(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self, None)

        self.ui = Ui_YaliMain()
        self.ui.setupUi(self)

        self.font = 10

        self.screenData = None
        # shortcut to open help
        self.helpShortCut = QtGui.QShortcut(QtGui.QKeySequence(Qt.Key_F1),self)

        # shortcut to open debug window
        #self.debugShortCut = QtGui.QShortcut(QtGui.QKeySequence(Qt.Key_F2),self)

        # something funny
        self.tetrisShortCut = QtGui.QShortcut(QtGui.QKeySequence(Qt.Key_F6),self)
        self.cursorShortCut = QtGui.QShortcut(QtGui.QKeySequence(Qt.Key_F7),self)
        self.themeShortCut  = QtGui.QShortcut(QtGui.QKeySequence(Qt.Key_F8),self)

        # shortcut to open a console
        self.consoleShortCut = QtGui.QShortcut(QtGui.QKeySequence(Qt.Key_F11),self)

        # set style
        self._style = ctx.flags.stylesheet
        self.updateStyle()

        # move one step at a time
        self.stepIncrement = 1

        # ToolButton Popup Menu
        self.popupMenu = QtGui.QMenu()
        self.shutDownAction = self.popupMenu.addAction(QtGui.QIcon(QtGui.QPixmap(":/images/system-shutdown.png")), _("Turn Off Computer"))
        self.rebootAction = self.popupMenu.addAction(QtGui.QIcon(QtGui.QPixmap(":/images/system-reboot.png")), _("Restart Computer"))
        self.restartAction = self.popupMenu.addAction(QtGui.QIcon(QtGui.QPixmap(":/images/system-yali-reboot.png")), _("Restart YALI"))
        #self.popupMenu.setDefaultAction(self.shutDownAction)
        self.ui.toolButton.setMenu(self.popupMenu)
        self.ui.toolButton.setDefaultAction(self.shutDownAction)

        # Main Slots
        self.connect(self.helpShortCut,     SIGNAL("activated()"),  self.slotToggleHelp)
        #self.connect(self.debugShortCut,    SIGNAL("activated()"),  self.toggleDebug)
        self.connect(self.consoleShortCut,  SIGNAL("activated()"),  self.toggleConsole)
        self.connect(self.cursorShortCut,   SIGNAL("activated()"),  self.toggleCursor)
        self.connect(self.themeShortCut,    SIGNAL("activated()"),  self.toggleTheme)
        self.connect(self.tetrisShortCut,   SIGNAL("activated()"),  self.toggleTetris)
        self.connect(self.ui.buttonNext,    SIGNAL("clicked()"),    self.slotNext)
        self.connect(self.ui.buttonBack,    SIGNAL("clicked()"),    self.slotBack)
        self.connect(self.ui.toggleHelp,    SIGNAL("clicked()"),    self.slotToggleHelp)
        self.connect(self.ui.releaseNotes,  SIGNAL("clicked()"),    self.showReleaseNotes)
        self.connect(self.popupMenu,        SIGNAL("triggered(QAction*)"), self.slotMenu)

        self._terminal = QTermWidget.QTermWidget()
        self._terminal.sendText("export TERM='xterm'\nclear\n")
        self.cmb = _("right")
        self.dontAskCmbAgain = False
        self.terminal = None
        self.tetris = None

        self.ui.helpContentFrame.hide()

        self.effect = QtGui.QGraphicsOpacityEffect(self)
        self.ui.mainStack.setGraphicsEffect(self.effect)
        self.effect.setOpacity(1.0)

        self.anime = QTimer(self)
        self.connect(self.anime, SIGNAL("timeout()"), self.animate)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton and not self.dontAskCmbAgain:
            if self.cmb == _("left"):
                ocmb = _("right")
            else:
                ocmb = _("left")
            reply = QuestionDialog(_("Mouse Settings"),
                                   _("You just clicked the <b>%s</b> mouse button.") % self.cmb,
                                   _("Do you want to switch to the <b>%s</b> handed configuration?") % ocmb,
                                   dontAsk = True)
            if reply == "yes":
                yali.sysutils.setMouse(self.cmb)
                self.cmb = ocmb
            elif reply == "dontask":
                self.dontAskCmbAgain = True

    def updateStyle(self):
        self.setStyleSheet(file(self._style).read())
        self.font = 10

    def setFontPlus(self):
        self._set_font(1)

    def setFontMinus(self):
        self._set_font(-1)

    def _set_font(self, num):
        # We have to edit style sheet to set new fonts
        # Because if you use a style sheet in your application
        # ::setFont gets useless :( http://doc.trolltech.com/4.5/qapplication.html#setFont
        old = "QWidget{font:%dpt;}" % self.font
        self.font = self.font + num
        new = "QWidget{font:%dpt;}" % self.font
        self.setStyleSheet(self.styleSheet().replace(old, new))

    def slotMenu(self, action):
        if action == self.shutDownAction:
            reply = QuestionDialog(_("Warning"),
                                   _("Are you sure you want to shut down your computer now?"))
            if reply == "yes":
                yali.util.shutdown()
        elif action == self.rebootAction:
            reply = QuestionDialog(_("Warning"),
                                   _("Are you sure you want to restart your computer now?"))
            if reply == "yes":
                yali.util.reboot()
        else:
            reply = QuestionDialog(_("Warning"),
                                   _("Are you sure you want to restart the YALI installer now?"))
            if reply == "yes":
                os.execv("/usr/bin/yali-bin", sys.argv)

    def toggleTheme(self):
        if self._style == ctx.flags.stylesheet:
            self._style = ctx.consts.alternatestylesheet
        else:
            self._style = ctx.flags.stylesheet
        self.updateStyle()

    def toggleConsole(self):
        if not self.terminal:
            self.terminal = Dialog(_("Terminal"), self._terminal, self, True, QtGui.QKeySequence(Qt.Key_F11))
            self.terminal.resize(700,500)
        self.terminal.exec_()

    def toggleTetris(self):
        self.tetris = Dialog(_("Tetris"), None, self, True, QtGui.QKeySequence(Qt.Key_F6))
        _tetris = Tetris(self.tetris)
        self.tetris.addWidget(_tetris)
        self.tetris.resize(240,500)
        _tetris.start()
        self.tetris.exec_()

    def toggleCursor(self):
        if self.cursor().shape() == QtGui.QCursor(Qt.ArrowCursor).shape():
            raw = QtGui.QPixmap(":/gui/pics/pardusman-icon.png")
            raw.setMask(raw.mask())
            self.setCursor(QtGui.QCursor(raw,2,2))
        else:
            self.unsetCursor()

    # show/hide help text
    def slotToggleHelp(self):
        self.ui.helpContentFrame.setFixedHeight(self.ui.helpContent.height())
        if self.ui.helpContentFrame.isVisible():
            self.ui.helpContentFrame.hide()
        else:
            self.ui.helpContentFrame.show()
        _w = self.ui.mainStack.currentWidget()
        _w.update()

    # show/hide debug window
    def toggleDebug(self):
        if ctx.debugger.isVisible():
            ctx.debugger.hideWindow()
        else:
            ctx.debugger.showWindow()

    # returns the id of current stack
    def getCurrent(self, d):
        new   = self.ui.mainStack.currentIndex() + d
        total = self.ui.mainStack.count()
        if new < 0: new = 0
        if new > total: new = total
        return new

    # move to id numbered step
    def setCurrent(self, id=None):
        if id:
            self.stackMove(id)

    # execute next step
    def slotNext(self,dryRun=False):
        widget = self.ui.mainStack.currentWidget()
        ret = True
        if not dryRun:
            ret = widget.execute()
        if ret:
            self.stackMove(self.getCurrent(self.stepIncrement))
            self.stepIncrement = 1

    # execute previous step
    def slotBack(self):
        widget = self.ui.mainStack.currentWidget()
        if widget.backCheck():
            self.stackMove(self.getCurrent(self.stepIncrement * -1))
        self.stepIncrement = 1

    # move to id numbered stack
    def stackMove(self, id):
        if not id == self.ui.mainStack.currentIndex() or id==0:
            self.effect.setOpacity(0.0)
            self.animationType = "fade-in"
            self.anime.start(50)
            self.ui.mainStack.setCurrentIndex(id)
            _w = self.ui.mainStack.currentWidget()
            self.ui.screenName.setText(_w.title)
            #self.ui.screenDescription.setText(_w.desc)
            self.ui.screenIcon.setPixmap(QtGui.QPixmap(":/gui/pics/%s.png" % (_w.icon)))
            self.ui.helpContent.setText(_w.help)
            # shown functions contain necessary instructions before
            # showing a stack ( updating gui, disabling some buttons etc. )

            ctx.mainScreen.processEvents()
            _w.update()
            ctx.mainScreen.processEvents()
            _w.shown()

    def animate(self):
        if self.animationType == "fade-in":
            if self.effect.opacity() < 1.0:
                self.effect.setOpacity(self.effect.opacity() + 0.2)
            else:
                self.anime.stop()
        if self.animationType == "fade-out":
            if self.effect.opacity() > 0.0:
                self.effect.setOpacity(self.effect.opacity() - 0.2)
            else:
                self.anime.stop()

    # create all widgets and add inside stack
    # see runner.py/_all_screens for the list
    def createWidgets(self, screens=[]):
        if not self.screenData:
            self.screenData = screens
        self.ui.mainStack.removeWidget(self.ui.page)
        for screen in screens:
            #if ctx.flags.debug:
                # debug all screens.
            #    weave_all_object_methods(ctx.aspect, screen)

            # enable navigation buttons before shown
            weave_object_method(enableNavButtonsAspect, screen, "shown")
            # disable navigation buttons before the execute.
            weave_object_method(disableNavButtonsAspect, screen, "execute")
            print "screen:%s" % screen
            self.ui.mainStack.addWidget(screen())

        #weave_all_object_methods(ctx.aspect, self)
        self.stackMove(0)

    # Enable/Disable buttons
    def disableNext(self):
        self.ui.buttonNext.setEnabled(False)

    def disableBack(self):
        self.ui.buttonBack.setEnabled(False)

    def enableNext(self):
        self.ui.buttonNext.setEnabled(True)

    def enableBack(self):
        self.ui.buttonBack.setEnabled(True)

    def isNextEnabled(self):
        return self.ui.buttonNext.isEnabled()

    def isBackEnabled(self):
        return self.ui.buttonBack.isEnabled()

    # processEvents
    def processEvents(self):
        QObject.emit(self, SIGNAL("signalProcessEvents"))

    def showReleaseNotes(self):
        # make a release notes dialog
        d = Dialog(_('Release Notes'), ReleaseNotes(self), self)
        d.resize(500,400)
        d.exec_()

class ReleaseNotes(QtGui.QTextBrowser):

    def __init__(self, *args):
        apply(QtGui.QTextBrowser.__init__, (self,) + args)

        self.setStyleSheet("background:white;color:black;")

        try:
            self.setText(codecs.open(self.load_file(), "r", "UTF-8").read())
        except Exception, msg:
            ctx.logger.error(_(msg))

    def load_file(self):
        rel_path = os.path.join(ctx.consts.source_dir,"release-notes/releasenotes-" + ctx.consts.lang + ".html")

        if not os.path.exists(rel_path):
            rel_path = os.path.join(ctx.consts.source_dir, "release-notes/releasenotes-en.html")
        if os.path.exists(rel_path):
            return rel_path
        raise Exception, _("Release notes could not be loaded.")
