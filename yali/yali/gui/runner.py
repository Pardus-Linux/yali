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

import mount
import reboot

import yali
import yali.gui.context as ctx
from pyaspects.weaver import *
from pyaspects.debuggeraspect import DebuggerAspect
from yali.gui.GuiAspects import *
from yali.gui.YaliDialog import Dialog

import YaliWindow
# screens
import Welcome
import Keyboard
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
             {'stage': 1, 'module': Keyboard},
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

        # default style and font
        self._app.setStyle("Windows")
        f = QFont( "Bitstream Vera Sans", 10);
        self._window.setFont(f)


        # add stages
        for stg in _all_stages:
            ctx.stages.addStage(stg['num'], stg['text'])

        # add screens
        num = 0
        da = DebuggerAspect(open(ctx.consts.log_file, "w"))
        for scr in _all_screens:
            w = scr['module'].Widget()

            # debug all screens.
            if ctx.options.debug == True:
                weave_all_object_methods(da, w)

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
# For testing
#        self._window.resize(800,600)

#        self._window.setActiveWindow()
        self._app.exec_loop()



def showException(ex_type, tb):
    title = "Unhandled Exception!"
    
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
        info.setText(_("An error occured!"))
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
            mount.umount(ctx.consts.target_dir + "/home")
        except:
            pass
        mount.umount(ctx.consts.target_dir)
        reboot.fastreboot()
