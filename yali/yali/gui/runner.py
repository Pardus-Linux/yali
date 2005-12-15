# -*- coding: utf-8 -*-
#
# Copyright (C) 2005, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#


import sys
from qt import *

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext


import yali
import yali.gui.context as ctx
from yali.gui.YaliDialog import Dialog

import YaliWindow
# screens
# FIXME: I haven't forget the localization part, just left it for later.
import Welcome
import AutoPartitioning
import Partitioning
import InstallSystem
import SetupRootpass
import SetupUsers
import SetupBootloader
import Goodbye


##
# Runner creates main GUI components for installation...
class Runner:

    _window = None
    _app = None

    def __init__(self):

        _all_stages = [
            {'num': 1, 'text': _("Prepare for install")},
            {'num': 2, 'text': _("Install system")},
            {'num': 3, 'text': _("Basic setup")}
            ]

        _all_screens = [
             {'stage': 1, 'module': Welcome},
             {'stage': 1, 'module': AutoPartitioning},
             {'stage': 1, 'module': Partitioning},
             {'stage': 2, 'module': InstallSystem},
             {'stage': 3, 'module': SetupRootpass},
             {'stage': 3, 'module': SetupUsers},
             {'stage': 3, 'module': SetupBootloader},
             {'stage': 3, 'module': Goodbye}
             ]

        self._app = QApplication(sys.argv)
        self._window = YaliWindow.Widget()

        # add stages
        for stg in _all_stages:
            ctx.stages.addStage(stg['num'], stg['text'])

        # add screens
        num = 0
        for scr in _all_screens:
            num += 1
            ctx.screens.addScreen(num, scr['stage'], scr['module'].Widget())


        self._app.connect(self._app, SIGNAL("lastWindowClosed()"),
                          self._app, SLOT("quit()"))

        self._app.connect(ctx.screens, PYSIGNAL("signalCurrent"),
                          ctx.stages.slotScreenChanged)

        self._app.connect(ctx.screens, PYSIGNAL("signalProcessEvents"),
                          self._app.processEvents)


        # set the current screen and stage to 1 at startup...
        ctx.stages.setCurrent(1)
        ctx.screens.setCurrent(1)


    ##
    # Fire up the interface.
    def run(self):

        self._window.show()
        # We want it to be a full-screen window.
        self._window.resize(self._app.desktop().size())
        self._window.move(0,0)
# For testing
#        self._window.resize(800,600)

#        self._window.setActiveWindow()
        self._app.exec_loop()



def showException(ex_type, tb):
    title = "Unhandled Exception!"
    
    if ex_type == yali.exception_fatal:
        w = ErrorWidget(tb)
    else:
        w = ExceptionWidget(tb)
    d = Dialog(title, w, None)
    d.resize(500,400)
    d.exec_loop()

    

class ExceptionWidget(QWidget):
    def __init__(self, tb_text, *args):
        apply(QWidget.__init__, (self,) + args)        

        info = QLabel(self)
        info.setText("Unhandled exception occured!")
        traceback = QTextView(self)
        traceback.setText(tb_text)

        l = QVBoxLayout(self)
        l.setSpacing(20)
        l.addWidget(info)
        l.addWidget(traceback)


class ErrorWidget(QWidget):
    def __init__(self, tb_text, *args):
        apply(QWidget.__init__, (self,) + args)        

        info = QLabel(self)
        info.setText(_("An error occured!"))
        traceback = QTextView(self)
        traceback.setText(tb_text)

        l = QVBoxLayout(self)
        l.setSpacing(20)
        l.addWidget(info)
        l.addWidget(traceback)
