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

from qt import *

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

import yali.sysutils
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.Ui.kickerwidget import KickerWidget
import yali.gui.context as ctx
from yali.gui.YaliDialog import Dialog
from yali.kickstart import yaliKickStart

def loadFile(path):
    """Read contents of a file"""
    f = file(path)
    data = f.read()
    f.close()
    return data

def get_kernel_opt(cmdopt):
    cmdline = loadFile("/proc/cmdline").split()
    for cmd in cmdline:
        pos = len(cmdopt)
        if cmd == cmdopt:
            return cmd
        if cmd.startswith(cmdopt) and cmd[pos] == '=':
            return cmd[pos+1:]
    return ''

def kickstartExists():
    if get_kernel_opt(ctx.consts.kickStartParam) or ctx.options.kickStartFile:
        return True
    return False

##
# Welcome screen is the first screen to be shown.
class Widget(KickerWidget, ScreenWidget):

    help = _('''
<font size="+2">Kicker Check !</font>
<p> Some help messages </p>
''')

    def __init__(self, *args):
        apply(KickerWidget.__init__, (self,) + args)

    def jumpToNext(self):
        num = ctx.screens.getCurrentIndex() + 1
        ctx.screens.goToScreen(num)

    def shown(self):
        if not kickstartExists():
            ctx.debugger.log("There is no kickstart jumps to the next screen.")
            self.jumpToNext()

        yaliKick = yaliKickStart()
        print "...",ctx.options.kickStartFile

        kickStartOpt = get_kernel_opt(ctx.consts.kickStartParam)

        if kickStartOpt:
            ctx.debugger.log("KICKSTART-PARAMS:: %s" % kickStartOpt)
            kickStartFile = kickStartOpt.splir(',')[1]
        else:
            kickStartFile = ctx.options.kickStartFile

        if kickStartFile:
            ctx.debugger.log("Reading Kickstart from file %s" % kickStartFile)
            yaliKick.readData(kickStartFile)
            if yaliKick.checkFileValidity()==True:
                ctx.debugger.log("File is ok")
                correctData = yaliKick.getValues()
                ctx.debugger.log("Root Pass is : %s" % correctData.rootPassword)
            else:
                ctx.debugger.log("This kickstart file is not correct !!")
                wrongData = yaliKick.getValues()
                ctx.debugger.log("".join(wrongData))

        ctx.screens.disablePrev()
        ctx.screens.disableNext()

