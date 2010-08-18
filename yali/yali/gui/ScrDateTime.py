# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2010 TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

from PyQt4 import QtGui
from PyQt4.QtCore import *

import os
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.Ui.datetimewidget import Ui_DateTimeWidget
import yali.gui.context as ctx
from yali.timezone import TimeZoneList
import yali.localedata

class Widget(QtGui.QWidget, ScreenWidget):
    title = _("Adjust Date and Time Settings")
    icon = "iconDate"
    help = _("""
<font size="+2">Date and Time</font>
<font size="+1">
<p>Date and time settings allows you to set the date and time of your computer. Generally,
you will also want to specify a correct timezone for your location in order to benefit
from automatic daylight saving time adjustments.
</p>
<p>
A timezone is a region of the earth that has uniform standard time, usually referred as the
local time. By convention, timezones compute their local time as an offset from UTC, the
Coordinated Universal Time.
</p>
</font>
""")

    def __init__(self, *args):
        QtGui.QWidget.__init__(self,None)
        self.ui = Ui_DateTimeWidget()
        self.ui.setupUi(self)
        self.timer = QTimer(self)
        self.fromTimeUpdater = True
        self.isDateChanged = False

        for country,data in yali.localedata.locales.items():
            if country == ctx.consts.lang:
                if data.has_key("timezone"):
                    ctx.installData.timezone = data["timezone"]

        # fill in the timezone list
        zom = TimeZoneList()
        zoneList = [ x.timeZone for x in zom.getEntries() ]
        zoneList.sort()
        for zone in zoneList:
            if zone == ctx.installData.timezone:
                self.currentZone = QtGui.QListWidgetItem(zone)
                self.ui.timeZoneList.addItem(self.currentZone)
            else:
                self.ui.timeZoneList.addItem(QtGui.QListWidgetItem(zone))

        # Widget connections
        self.connect(self.ui.timeHours, SIGNAL("timeChanged(QTime)"),self.timerStop)
        self.connect(self.ui.timeMinutes, SIGNAL("timeChanged(QTime)"),self.timerStop)
        self.connect(self.ui.timeSeconds, SIGNAL("timeChanged(QTime)"),self.timerStop)
        self.connect(self.ui.calendarWidget, SIGNAL("selectionChanged()"),self.dateChanged)
        self.connect(self.timer, SIGNAL("timeout()"),self.updateClock)

        # Select the timeZone
        self.ui.timeZoneList.setCurrentItem(self.currentZone)
        self.timer.start(1000)

    def dateChanged(self):
        self.isDateChanged = True

    def timerStop(self,i):
        if self.fromTimeUpdater:
            return
        # Human action detected; stop the timer.
        self.timer.stop()

    def updateClock(self):

        # What time is it ?
        cur = QTime.currentTime()

        self.fromTimeUpdater = True
        self.ui.timeHours.setTime(cur)
        self.ui.timeMinutes.setTime(cur)
        self.ui.timeSeconds.setTime(cur)
        self.fromTimeUpdater = False

    def shown(self):
        self.timer.start(1000)

    def setTime(self):
        ctx.yali.setTime(self.ui)

    def execute(self):
        if not self.timer.isActive() or self.isDateChanged:
            QTimer.singleShot(500,self.setTime)
            self.timer.stop()

        ctx.yali.setTimeZone(self.ui)

        return True
