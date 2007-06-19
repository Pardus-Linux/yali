# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

import os
from qt import *

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

import yali.localedata
import yali.localeutils
from yali.gui.YaliDialog import Dialog, WarningDialog, WarningWidget
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.Ui.networkwidget import NetworkWidget
import yali.gui.context as ctx

##
# Network setup screen
class Widget(NetworkWidget, ScreenWidget):

    help = _('''
<font size="+2">Network Setup</font>

<font size="+1">
<p>
Select the location of the machine or use Manual Configuration.<br>
You can add printers by using printer section.
</p>
</font>
''')

    def __init__(self, *args):
        apply(NetworkWidget.__init__, (self,) + args)
        self.serverList = ServerList(self.list_clients)
        for wig in [self.list_clients,self.list_printers]:
            wig.setPaletteBackgroundColor(ctx.consts.bg_color)
            wig.setPaletteBackgroundColor(ctx.consts.bg_color)
        
        for server in self.serverList.list:
            self.list_clients.insertItem(server)
                
        self.connect(self.list_clients,SIGNAL("selectionChanged(QListBoxItem*)"),self.slotLayoutChanged)
        self.connect(self.check_manuel,SIGNAL("toggled(bool)"),self.frame3.setEnabled)
        self.connect(self.check_manuel,SIGNAL("toggled(bool)"),self.list_clients.setDisabled)

    def shown(self):
        from os.path import basename
        ctx.debugger.log("%s loaded" % basename(__file__))

    def execute(self):
        # show confirmation dialog
        w = WarningWidget(self)
        w.setMessage(_('''<b>
<p>Do you want to continue ?</p>
</b>
'''))
        
        self.dialog = WarningDialog(w, self)
        if not self.dialog.exec_loop():
            ctx.screens.enablePrev()
            ctx.screens.enableNext()
            return False
        return True

    def slotLayoutChanged(self, server):
        self.list_printers.clear()
        self.line_gateway.setText(server.serverData.gateway)
        #self.line_subnet.setText(server.serverData.subnet)
        self.line_ip.setText(server.serverData.ip_address)
        self.line_machineName.setText(server.serverData.name)
        for printer in server.serverData.printers:
            ctx.debugger.log(printer)
            self.list_printers.insertItem(printer)

class ServerList:
    def __init__(self,parent,filePath=ctx.consts.serverList):
        self.list = []
        print filePath
        for line in open(filePath):
            srv = Server()
            srv.name, srv.ip_address, srv.gateway, srv.serverType, srv.numberOfClients, srv.upsIp, printers = line.split(";")
            srv.printers = []
            if printers.find(","):
                _prs = map(lambda x: x.strip("\n"),printers.split(","))
                srv.printers.append(_prs[0])
                _pre = _prs[0][:-2]
                _prs.remove(_prs[0])
                for i in _prs:
                    srv.printers.append(_pre + i)
            else:
                srv.printers.append(printers)
            self.list.append(ServerItem(parent,srv))

class Server:
    pass

class ServerItem(QListBoxText):
    def __init__(self, parent, serverData):
        text = serverData.name
        self.serverData = serverData
        apply(QListBoxText.__init__, (self,parent,text))
