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
import yali.storage

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
        ctx.kickerReady = False
        if not kickstartExists():
            ctx.debugger.log("There is no kickstart jumps to the next screen.")
            self.jumpToNext()

        ctx.autoInstall = True
        yaliKick = yaliKickStart()
        print "...",ctx.options.kickStartFile

        kickStartOpt = get_kernel_opt(ctx.consts.kickStartParam)

        if kickStartOpt:
            ctx.debugger.log("KICKSTART-PARAMS:: %s" % kickStartOpt)
            kickStartFile = kickStartOpt.split(',')[1]
        else:
            kickStartFile = ctx.options.kickStartFile

        if kickStartFile:
            ctx.debugger.log("Reading Kickstart from file %s" % kickStartFile)
            yaliKick.readData(kickStartFile)
            if yaliKick.checkFileValidity()==True:
                ctx.debugger.log("File is ok")

                # find usable storage devices
                # initialize all storage devices
                if not yali.storage.init_devices():
                    raise GUIException, _("Can't find a storage device!")

                devices = []
                for dev in yali.storage.devices:
                    if dev.getTotalMB() >= ctx.consts.min_root_size:
                        devices.append(dev)

                correctData = yaliKick.getValues()
                ctx.debugger.log("Given KickStart Values :")

                # single types
                ctx.installData.keyData = correctData.keyData
                ctx.installData.rootPassword = correctData.rootPassword
                ctx.installData.hostName = correctData.hostname
                ctx.installData.autoLoginUser = correctData.autoLoginUser
                ctx.installData.autoPartDev = devices[int(correctData.partitioning[0].disk[-1])]

                ctx.debugger.log("HOSTNAME : %s " % ctx.installData.hostName)
                ctx.debugger.log("KEYDATA  : %s " % ctx.installData.keyData.X)

                # multi types
                for user in correctData.users:
                    ctx.installData.users.append(user)
                    yali.users.pending_users.append(user)
                    ctx.debugger.log("USER    : %s " % user.username)

                ctx.screens.processEvents()
                ctx.kickerReady = True
                ctx.screens.next()
            else:
                ctx.debugger.log("This kickstart file is not correct !!")
                wrongData = yaliKick.getValues()
                ctx.debugger.log("".join(wrongData))

        ctx.screens.disablePrev()
        ctx.screens.disableNext()

