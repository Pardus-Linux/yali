# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2007, TUBITAK/UEKAE
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
import yali.sysutils
import yali.gui.context as ctx
from pyaspects.weaver import *
from yali.gui.aspects import *
from yali.gui.YaliDialog import Dialog
from yali.gui.debugger import Debugger
from yali.gui.debugger import DebuggerAspect

import YaliWindow
# screens
import ScrWelcome
import ScrCheckCD
import ScrKeyboard
import ScrPartitionAuto
import ScrPartitionManual
import ScrInstall
import ScrAdmin
import ScrUsers
import ScrBootloader
import ScrGoodbye
import ScrNetwork

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
             {'stage': 1, 'module': ScrWelcome},
             {'stage': 1, 'module': ScrCheckCD},
             {'stage': 1, 'module': ScrKeyboard},
            #{'stage': 1, 'module': ScrNetwork},
             {'stage': 1, 'module': ScrPartitionAuto},
             {'stage': 1, 'module': ScrPartitionManual},
             {'stage': 2, 'module': ScrInstall},
             {'stage': 3, 'module': ScrAdmin},
             {'stage': 3, 'module': ScrUsers},
             {'stage': 3, 'module': ScrBootloader},
             {'stage': 3, 'module': ScrGoodbye}
             ]

        self._app = QApplication(sys.argv)
        self._window = YaliWindow.Widget()

        # default style and font
        self._app.setStyle("Windows")
        f = QFont("Bitstream Vera Sans", 10);
        self._window.setFont(f)

        ctx.debugger = Debugger()
        
        # visual debug mode
        if ctx.options.debug == True or yali.sysutils.checkYaliDebug():
            ctx.debugger.showWindow()
        
        ctx.debugger.log("Yali Started")
        
        # add stages
        for stg in _all_stages:
            ctx.stages.addStage(stg['num'], stg['text'])

        # add screens
        num = 0
        for scr in _all_screens:
            w = scr['module'].Widget()

            if ctx.options.debug == True or yali.sysutils.checkYaliDebug():
                # debug all screens.
                weave_all_object_methods(ctx.debugger.aspect, w)

            # enable navigation buttons before shown
            weave_object_method(enableNavButtonsAspect, w, "shown")

            # disable navigation buttons before the execute.
            weave_object_method(disableNavButtonsAspect, w, "execute")

            num += 1
            ctx.screens.addScreen(num, scr['stage'], w)

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
        self._app.exec_loop()

def showException(ex_type, tb):
    title = _("Error!")
    
    if ex_type in (yali.exception_fatal, yali.exception_pisi):
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
        l.setSpacing(10)
        l.addWidget(info)
        l.addWidget(traceback)

class ErrorWidget(QWidget):
    def __init__(self, tb_text, *args):
        apply(QWidget.__init__, (self,) + args)        

        info = QLabel(self)
        info.setText(_("Unhandled error occured!"))
        traceback = QTextView(self)
        traceback.setText(tb_text)

        reboot_button = QPushButton(self)
        reboot_button.setText(_("Reboot System!"))

        l = QVBoxLayout(self)
        l.setSpacing(10)
        l.addWidget(info)
        l.addWidget(traceback)

        b = QHBoxLayout(l)
        b.setMargin(5)
        b.addStretch(1)
        b.addWidget(reboot_button)

        self.connect(reboot_button, SIGNAL("clicked()"),
                     self.slotReboot)

    def slotReboot(self):
        try:
            yali.sysutils.umount(ctx.consts.target_dir + "/home")
        except:
            pass
        yali.sysutils.umount(ctx.consts.target_dir)
        yali.sysutils.fastreboot()
