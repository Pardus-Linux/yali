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

# linux ?
import os
import dbus
import time
import shutil

# we need i18n
import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

# PyQt4 Rocks
from PyQt4 import QtGui
from PyQt4.QtCore import *

# yali base
from yali.exception import *
from yali.constants import consts
from yali.gui.installdata import *
import yali.gui.context as ctx
import yali.localeutils
import yali.sysutils
import yali.fstab
from pardus.sysutils import get_kernel_option

# pisi base
import pisi.ui
import yali.pisiiface

# partitioning
#import yali.partitiontype as parttype
#import yali.partitionrequest as request
#from yali.partitionrequest import partrequests
#from yali.parteddata import *

# gui
from yali.gui.YaliDialog import Dialog, QuestionDialog, InfoDialog, InformationWindow, MesssageWindow

# debugger
from yali.gui.debugger import Debugger
from yali.gui.debugger import DebuggerAspect

# screens
import yali.gui.ScrKahyaCheck
import yali.gui.ScrWelcome
import yali.gui.ScrCheckCD
import yali.gui.ScrKeyboard
import yali.gui.ScrDateTime
import yali.gui.ScrAdmin
import yali.gui.ScrUsers
import yali.gui.ScrPartitionAuto
import yali.gui.ScrPartitionManual
import yali.gui.ScrBootloader
import yali.gui.ScrInstallationAuto
import yali.gui.ScrInstall
import yali.gui.ScrSummary
import yali.gui.ScrGoodbye
import yali.gui.ScrRescue
import yali.gui.ScrRescueGrub
import yali.gui.ScrRescuePisi
import yali.gui.ScrRescuePassword
import yali.gui.ScrRescueFinish

PARTITION_ERASE_ALL, PARTITION_USE_AVAIL, PARTITION_USE_OLD = range(3)

class Yali:
    def __init__(self, install_type=YALI_INSTALL, install_plugin=None):

        self._screens = {}

        # Normal Installation process
        self._screens[YALI_INSTALL] = [                                  # Numbers can be used with -s paramter
                                       yali.gui.ScrKahyaCheck,          # 00
                                       yali.gui.ScrWelcome,             # 01
                                       yali.gui.ScrCheckCD,             # 02
                                       yali.gui.ScrKeyboard,            # 03
                                       yali.gui.ScrDateTime,            # 04
                                       yali.gui.ScrUsers,               # 05
                                       yali.gui.ScrAdmin,               # 06
                                       yali.gui.ScrPartitionAuto,       # 07
                                       yali.gui.ScrPartitionManual,     # 08
                                       yali.gui.ScrBootloader,          # 09
                                       yali.gui.ScrSummary,             # 10
                                       yali.gui.ScrInstall,             # 11
                                       yali.gui.ScrGoodbye              # 12
                                      ]

        self._screens[YALI_DVDINSTALL] = [                              # Numbers can be used with -s paramter
                                       yali.gui.ScrKahyaCheck,          # 00
                                       yali.gui.ScrWelcome,             # 01
                                       yali.gui.ScrCheckCD,             # 02
                                       yali.gui.ScrKeyboard,            # 03
                                       yali.gui.ScrDateTime,            # 04
                                       yali.gui.ScrUsers,               # 05
                                       yali.gui.ScrAdmin,               # 06
                                       yali.gui.ScrPartitionAuto,       # 07
                                       yali.gui.ScrPartitionManual,     # 08
                                       yali.gui.ScrBootloader,          # 09
                                       yali.gui.ScrInstallationAuto,    # 10
                                       yali.gui.ScrSummary,             # 11
                                       yali.gui.ScrInstall,             # 12
                                       yali.gui.ScrGoodbye              # 13
                                      ]

        # FirstBoot Installation process
        self._screens[YALI_FIRSTBOOT] = [                                # Numbers can be used with -s paramter
                                         yali.gui.ScrWelcome,           # 00
                                         yali.gui.ScrKeyboard,          # 01
                                         yali.gui.ScrDateTime,          # 02
                                         yali.gui.ScrUsers,             # 03
                                         yali.gui.ScrAdmin,             # 04
                                         yali.gui.ScrGoodbye            # 05
                                        ]

        # Oem Installation process
        self._screens[YALI_OEMINSTALL] = [                                  # Numbers can be used with -s paramter
                                          yali.gui.ScrWelcome,             # 00
                                          yali.gui.ScrCheckCD,             # 01
                                          yali.gui.ScrPartitionAuto,       # 02
                                          yali.gui.ScrPartitionManual,     # 03
                                          yali.gui.ScrBootloader,          # 04
                                          yali.gui.ScrSummary,             # 05
                                          yali.gui.ScrInstall,             # 06
                                          yali.gui.ScrGoodbye              # 07
                                         ]

        # Use YALI just for partitioning
        self._screens[YALI_PARTITIONER] = [
                                           yali.gui.ScrPartitionManual  # Manual Partitioning
                                          ]

        # Rescue Mode
        self._screens[YALI_RESCUE] = [
                                      yali.gui.ScrRescue,            # Rescue Mode
                                      yali.gui.ScrRescueGrub,        # Grub Rescue
                                      yali.gui.ScrRescuePisi,        # Pisi HS Rescue
                                      yali.gui.ScrRescuePassword,    # Password Rescue
                                      yali.gui.ScrRescueFinish       # Final step for rescue
                                     ]

        self.plugin = None

        # mutual exclusion
        self.mutex = QMutex()
        self.waitCondition = QWaitCondition()
        self.retryAnswer = False

        # Let the show begin..
        if install_type == YALI_PLUGIN:
            self.plugin  = self.getPlugin(install_plugin)
            if self.plugin:
                self.screens = self.plugin.config.screens
                # run plugins setup
                self.plugin.config.setup()
            else:
                install_type = YALI_INSTALL
                InfoDialog(_("Plugin '%s' could not be loaded or found, switching to normal installation process." % install_plugin))

        if not self.plugin:
            self.screens = self._screens[install_type]

        self.install_type = install_type
        self.info = InformationWindow("Please wait...")
        self.checkCDStop = True

    def messageWindow(self, title, text, type="ok", default=None, customButtons=None, customIcon=None):
        return MesssageWindow(title, text, type, default, customButtons, customIcon, run=True).rc

    def getPlugin(self, p):
        try:
            _p = __import__("yali.plugins.%s.config" % p)
        except ImportError:
            return False
        plugin = getattr(_p.plugins,p)
        return plugin

    def checkCD(self, rootWidget):
        ctx.mainScreen.disableNext()
        ctx.mainScreen.disableBack()

        self.info.updateAndShow(_("Starting validation..."))
        class PisiUI(pisi.ui.UI):
            def notify(self, event, **keywords):
                pass
            def display_progress(self, operation, percent, info, **keywords):
                pass

        yali.pisiiface.initialize(ui = PisiUI(), with_comar = False, nodestDir = True)
        yali.pisiiface.addCdRepo()
        ctx.mainScreen.processEvents()
        pkg_names = yali.pisiiface.getAvailablePackages()

        rootWidget.progressBar.setMaximum(len(pkg_names))

        cur = 0
        for pkg_name in pkg_names:
            cur += 1
            ctx.debugger.log("Validating %s " % pkg_name)
            self.info.updateMessage(_("Validating %s") % pkg_name)
            if self.checkCDStop:
                continue
            try:
                yali.pisiiface.checkPackageHash(pkg_name)
                rootWidget.progressBar.setValue(cur)
            except:
                self.showError(_("Validation Failed"),
                               _("<b><p>Validation of installation packages failed.\
                                  Please remaster your installation medium and restart the installation.</p></b>"))

        if not self.checkCDStop:
            rootWidget.checkLabel.setText(_('<font color="#FFF"><b>Validation succeeded. You can proceed with the installation.</b></font>'))
            rootWidget.checkButton.setText(_("Validate Integrity"))
        else:
            rootWidget.checkLabel.setText("")
            rootWidget.progressBar.setValue(0)

        yali.pisiiface.removeRepo(ctx.consts.cd_repo_name)

        ctx.mainScreen.enableNext()
        ctx.mainScreen.enableBack()

        self.info.hide()

    def setKeymap(self, keymap):
        yali.localeutils.setKeymap(keymap["xkblayout"], keymap["xkbvariant"])
        ctx.installData.keyData = keymap

    def setTime(self, rootWidget):
        self.info.updateAndShow(_("Adjusting time settings..."))
        date = rootWidget.calendarWidget.selectedDate()
        args = "%02d%02d%02d%02d%04d.%02d" % (date.month(), date.day(),
                                              rootWidget.timeHours.time().hour(), rootWidget.timeMinutes.time().minute(),
                                              date.year(), rootWidget.timeSeconds.time().second())

        # Set current date and time
        ctx.debugger.log("Date/Time setting to %s" % args)
        yali.sysutils.run("date %s" % args)

        # Sync date time with hardware
        ctx.debugger.log("YALI's time is syncing with the system.")
        yali.sysutils.run("hwclock --systohc")
        self.info.hide()

    def setTimeZone(self, rootWidget):
        # Store time zone selection we will set it in processPending actions.
        ctx.installData.timezone = rootWidget.timeZoneList.currentItem().text()
        ctx.debugger.log("Time zone selected as %s " % ctx.installData.timezone)

    def scanPartitions(self, rootWidget):

        def sortBySize(x,y):
            if x["newSize"]>y["newSize"]:return -1
            elif x["newSize"]==y["newSize"]: return 0
            return 1

        self.info.updateAndShow(_("Analyzing disks..."))

        rootWidget.resizablePartitions = []
        rootWidget.resizableDisks = []
        rootWidget.freeSpacePartitions = []
        rootWidget.freeSpaceDisks = []

        ctx.debugger.log("Disk analysis started.")
        ctx.debugger.log("%d disk found." % len(yali.storage.devices))
        for dev in yali.storage.devices:
            ctx.debugger.log("In disk %s, %d mb is free." % (dev.getPath(), dev.getLargestContinuousFreeMB()))
            #if dev.getLargestContinuousFreeMB() > ctx.consts.min_root_size + 100:
            #    rootWidget.resizableDisks.append(dev)
            for part in dev.getOrderedPartitionList():
                ctx.debugger.log("Partition %s found on disk %s, formatted as %s" % (part.getPath(), dev.getPath(), part.getFSName()))
                if part.isFreespace() and (part.isLogical() or dev.primaryAvailable()):
                    ctx.debugger.log(" - This partition is free")
                    if part.getMB() > ctx.consts.min_root_size:
                        ctx.debugger.log(" - Usable size for this partition is %.2f MB" % part.getMB())
                        rootWidget.freeSpacePartitions.append({"partition":part,"newSize":part.getMB()})
                        if dev not in rootWidget.freeSpaceDisks:
                            rootWidget.freeSpaceDisks.append(dev)
                elif part.isResizable():
                    minSize = part.getMinResizeMB()
                    possibleFreeSize = part.getMB() - minSize
                    ctx.debugger.log(" - This partition is resizable")
                    ctx.debugger.log(" - Total size of this partition is %.2f MB" % part.getMB())
                    ctx.debugger.log(" - It can resizable to %.2f MB" % minSize)
                    ctx.debugger.log(" - Usable size for this partition is %.2f MB" % possibleFreeSize)
                    rootWidget.resizablePartitions.append({"partition":part,"newSize":possibleFreeSize})
                    if possibleFreeSize / 2 > ctx.consts.min_root_size:
                        if dev not in rootWidget.resizableDisks:
                            rootWidget.resizableDisks.append(dev)
                else:
                    ctx.debugger.log("This partition is not usable")

        # Sort by size..
        rootWidget.resizablePartitions.sort(sortBySize)
        rootWidget.freeSpacePartitions.sort(sortBySize)

        self.info.hide()

    def getResizableFirstPartition(self):
        # Hacky .. :)
        arp = []
        class __v:
            pass
        mean = __v()
        self.scanPartitions(mean)
        for partition in mean.resizablePartitions:
            if partition["newSize"] / 2 >= ctx.consts.min_root_size:
                arp.append(partition)
        if len(arp)>0:
            return arp[0]
        else:
            raise YaliException, "No resizable partition found!"

    def autoPartDevice(self):
        self.info.updateAndShow(_("Writing partition table(s)..."))

        ctx.partrequests.remove_all()
        dev = ctx.installData.autoPartDev

        # first delete partitions on device
        dev.deleteAllPartitions()
        dev.commit()

        ctx.mainScreen.processEvents()

        p = dev.addPartition(None,
                             parttype.root.parted_type,
                             parttype.root.filesystem,
                             dev.getFreeMB(),
                             parttype.root.parted_flags)
        p = dev.getPartition(p.num) # get partition.Partition

        # create the partition
        dev.commit()
        ctx.mainScreen.processEvents()

        # make partition requests
        ctx.partrequests.append(request.MountRequest(p, parttype.root))
        ctx.partrequests.append(request.FormatRequest(p, parttype.root))
        ctx.partrequests.append(request.LabelRequest(p, parttype.root))
        ctx.partrequests.append(request.SwapFileRequest(p, parttype.root))

        time.sleep(2)

    def checkSwap(self):
        # check swap partition, if not present use swap file
        rt = request.mountRequestType
        pt = parttype.swap
        swap_part_req = ctx.partrequests.searchPartTypeAndReqType(pt, rt)

        if not swap_part_req:
            # No swap partition defined using swap as file in root
            # partition
            rt = request.mountRequestType
            pt = parttype.root
            root_part_req = ctx.partrequests.searchPartTypeAndReqType(pt, rt)
            ctx.partrequests.append(request.SwapFileRequest(root_part_req.partition(),
                                    root_part_req.partitionType()))

    def autoPartUseAvail(self):
        dev = ctx.installData.autoPartDev
        _part = ctx.installData.autoPartPartition
        part = _part["partition"]

        if part.isLogical():
            ptype = PARTITION_LOGICAL
        else:
            ptype = PARTITION_PRIMARY

        if part.isResizable():
            newPartSize = int(_part["newSize"]/2) - 2
            ctx.debugger.log("UA: newPartSize : %s " % newPartSize)
            ctx.debugger.log("UA: resizing to : %s " % (int(part.getMB()) - newPartSize))

            try:
                _np = dev.resizePartition(part._fsname, part.getMB() - newPartSize, part)
            except FSCheckError, message:
                ctx.debugger.log("FAILED: %s" % unicode(message))
                InfoDialog(unicode(message), title = _("Filesystem Error"))

            self.info.updateMessage(_("Finished resizing partition(s)"))
            ctx.debugger.log("UA: Resize finished.")
            time.sleep(1)

            newStart = _np.geom.end
            np = dev.getPartition(_np.num)
            self.info.updateMessage(_("Creating new partition..."))
            ctx.debugger.log("UA: newStart : %s " % newStart)
            _newPart = dev.addPartition(None,
                                        ptype,
                                        parttype.root.filesystem,
                                        newPartSize - 8,
                                        parttype.root.parted_flags,
                                        newStart)
            newPart = dev.getPartition(_newPart.num)
        elif part.isFreespace():
            newPartSize = part.getMB() - 8
            newStart = part.getStart()
            _newPart = dev.addPartition(part._partition,
                                        ptype,
                                        parttype.root.filesystem,
                                        newPartSize,
                                        parttype.root.parted_flags)
            newPart = dev.getPartition(_newPart.num)
        else:
            raise YaliError, _("Failed to use partition '%s' for automatic installation.") % part.getPath()

        dev.commit()
        ctx.mainScreen.processEvents()

        # make partition requests
        ctx.partrequests.append(request.MountRequest(newPart, parttype.root))
        ctx.partrequests.append(request.FormatRequest(newPart, parttype.root))
        ctx.partrequests.append(request.LabelRequest(newPart, parttype.root))
        ctx.partrequests.append(request.SwapFileRequest(newPart, parttype.root))

        time.sleep(2)

    def guessBootLoaderDevice(self, root_part=None):
        if len(yali.storage.devices) > 1 or ctx.isEddFailed:
            #opts = get_kernel_option("mudur")
            opts = yali.sysutils.liveMediaSystem()
            if opts.__eq__("harddisk"):
                ctx.installData.bootLoaderDev = os.path.basename(ctx.installData.orderedDiskList[1])
            else:
                ctx.installData.bootLoaderDev = os.path.basename(ctx.installData.orderedDiskList[0])
        else:
            if root_part:
                pardus_path = root_part
            else:
                root_part_req = ctx.partrequests.searchPartTypeAndReqType(parttype.root,
                                                                          request.mountRequestType)
                if not root_part_req:
                    raise YaliException, "No Root Part request found !"
                pardus_path = root_part_req.partition().getPath()

            if pardus_path.find("cciss") > 0:
                # HP Smart array controller (something like /dev/cciss/c0d0p1)
                ctx.installData.bootLoaderDev = pardus_path[:-2]
            else:
                ctx.installData.bootLoaderDev = str(filter(lambda u: not u.isdigit(),
                                                           os.path.basename(pardus_path)))
        return ctx.installData.bootLoaderDev

    def fillFstab(self):
        # fill fstab
        fstab = yali.fstab.Fstab()
        for req in ctx.partrequests:
            req_type = req.requestType()
            if req_type == request.mountRequestType:
                p = req.partition()
                pt = req.partitionType()

                # Use default label for root partition (PARDUS_ROOT)
                # TODO: Trigger udev to get new label info.
                ####
                path = "LABEL=%s" % p.getTempLabel()

                fs = pt.filesystem._sysname or pt.filesystem._name
                mountpoint = pt.mountpoint
                # TODO: consider merging mountoptions in filesystem.py
                opts = ",".join([pt.filesystem.mountOptions(), pt.mountoptions])

                e = yali.fstab.FstabEntry(path, mountpoint, fs, opts)
                fstab.insert(e)
            elif req_type == request.swapFileRequestType:
                path = "/" + ctx.consts.swap_file_name
                # Look bug #9233
                mountpoint = "swap"
                fs = "swap"
                opts = "sw"
                e = yali.fstab.FstabEntry(path, mountpoint, fs, opts)
                fstab.insert(e)
        fstab.close()

    def backupInstallData(self):
        import piksemel

        def insert(root,tag,data):
            _ = root.insertTag(tag)
            _.insertData(str(data))

        # let create a yali piksemel..
        yali = piksemel.newDocument("yali")

        # let store keymap and language options
        insert(yali,"language",ctx.consts.lang)
        insert(yali,"keymap",ctx.installData.keyData["xkblayout"])
        insert(yali,"variant",ctx.installData.keyData["xkbvariant"])

        # we will store passwords as shadowed..
        insert(yali,"root_password",yali.sysutils.getShadowed(ctx.installData.rootPassword or ""))

        # time zone..
        insert(yali,"timezone",ctx.installData.timezone)

        # hostname ..
        insert(yali,"hostname",ctx.installData.hostName)

        # users ..
        if len(yali.users.pending_users) > 0:
            users = yali.insertTag("users")
        for u in yali.users.pending_users:
            user = users.insertTag("user")
            insert(user,"username",u.username)
            insert(user,"realname",u.realname)
            insert(user,"password",yali.sysutils.getShadowed(u.passwd))
            insert(user,"groups",",".join(u.groups))

        # partitioning ..
        devices = []
        for dev in yali.storage.devices:
            if dev.getTotalMB() >= ctx.consts.min_root_size:
                devices.append(dev.getPath())

        partitioning = yali.insertTag("partitioning")
        partitioning.setAttribute("partition_type",
                                 {methodEraseAll:"auto",
                                  methodUseAvail:"smartAuto",
                                  methodManual:"manual"}[ctx.installData.autoPartMethod])
        if not ctx.installData.autoPartMethod == methodManual:
            try:
                partitioning.insertData("disk%d" % devices.index(ctx.installData.autoPartDev.getPath()))
            except:
                partitioning.insertData(ctx.installData.autoPartDev.getPath())

        ctx.installData.sessionLog = yali.toPrettyString()
        # ctx.debugger.log(yali.toPrettyString())

    def processPendingActions(self, rootWidget):
        rootWidget.steps.setOperations([{"text":_("Connecting to D-Bus..."),"operation":yali.postinstall.connectToDBus}])

        steps = [{"text":_("Setting hostname..."),"operation":yali.postinstall.setHostName},
                 {"text":_("Setting timezone..."),"operation":yali.postinstall.setTimeZone},
                 {"text":_("Setting root password..."),"operation":yali.postinstall.setRootPassword},
                 {"text":_("Adding users..."),"operation":yali.postinstall.addUsers},
                 {"text":_("Setting console keymap..."),"operation":yali.postinstall.writeConsoleData},
                 {"text":_("Migrating Xorg configuration..."),"operation":yali.postinstall.migrateXorgConf}]

        stepsBase = [{"text":_("Copying repository index..."),"operation":yali.postinstall.copyPisiIndex},
                    # FIXME: This is weird, look at setPackages
                     {"text":_("Configuring other packages..."),"operation":yali.postinstall.setPackages},
                     {"text":_("Installing Bootloader..."),"operation":self.installBootloader}]

        if self.install_type in [YALI_INSTALL, YALI_DVDINSTALL, YALI_FIRSTBOOT]:
            rootWidget.steps.setOperations(steps)
        elif self.install_type == YALI_PLUGIN:
            rootWidget.steps.setOperations(self.plugin.config.steps)

        rootWidget.steps.setOperations(stepsBase)

    def installBootloader(self, pardusPart = None):
        if not ctx.installData.bootLoaderDev:
            ctx.debugger.log("Don't install bootloader selected; skipping.")
            return

        loader = yali.bootloader.BootLoader()

        # Predefined Pardus path for rescue mode
        if pardusPart:
            _ins_part = pardusPart.getPath()
            _ins_part_label = pardusPart.getTempLabel() or pardusPart.getFSLabel()
            grubConfPath = os.path.join(ctx.consts.target_dir,"boot/grub/grub.conf")
            if os.path.exists(grubConfPath):
                # Rename the old config we will create a new one
                os.rename(grubConfPath, grubConfPath + ".old")
        else:
            root_part_req = ctx.partrequests.searchPartTypeAndReqType(parttype.root,
                                                                      request.mountRequestType)
            _ins_part = root_part_req.partition().getPath()
            _ins_part_label = root_part_req.partition().getTempLabel() or pardusPart.getFSLabel()

        loader.writeGrubConf(_ins_part, ctx.installData.bootLoaderDev, _ins_part_label)

        # If selected, Check for Windows Partitions
        # FIXME We need to use pardus.grubutils addEntry method for adding found Windows entries
        if ctx.installData.bootLoaderDetectOthers:

            ctx.debugger.log("Checking for other operating systems (Windows)")
            for d in yali.storage.devices:
                for p in d.getPartitions():
                    fs = p.getFSName()
                    if fs in ("ntfs", "fat32"):
                        if yali.sysutils.isWindowsBoot(p.getPath(), fs):
                            ctx.debugger.log("Windows found on device %s partition %s " % (p.getDevicePath(), p.getPath()))
                            win_fs = fs
                            win_dev = os.path.basename(p.getDevicePath())
                            win_root = os.path.basename(p.getPath())
                            loader.grubConfAppendWin(ctx.installData.bootLoaderDev,
                                                     win_dev,
                                                     win_root,
                                                     win_fs)
                            continue

        # Pardus Grub utils
        import pardus.grubutils

        # Parse current grub.conf which includes installed release entry and Win entries if exists
        grubConf = pardus.grubutils.grubConf()
        grubConfPath = os.path.join(ctx.consts.target_dir,"boot/grub/grub.conf")
        grubConf.parseConf(grubConfPath)

        # If selected, Check for Linux Partitions
        if ctx.installData.bootLoaderDetectOthers:

            def _update_dev(old, new):
                # If it fails
                try:
                    return "(%s," % new + old.split(',')[1]
                except:
                    ctx.debugger.log("UD: Failed, new: %s -- old: %s" % (new, old))
                    ctx.debugger.log("UD: Failed, using old: %s" % old)
                    return old

            ctx.debugger.log("Checking for other distributions (Linux)")
            for d in yali.storage.devices:
                for p in d.getPartitions():
                    fs = p.getFSName()
                    if fs in ("ext4", "ext3", "reiserfs", "xfs") and not p.getPath() == _ins_part:
                        ctx.debugger.log("Partition found which has usable fs (%s)" % p.getPath())
                        guest_grub_conf = yali.sysutils.isLinuxBoot(p.getPath(), fs)
                        if guest_grub_conf:
                            ctx.debugger.log("GRUB Found on device %s partition %s " % (p.getDevicePath(), p.getPath()))
                            guestGrubConf = pardus.grubutils.grubConf()
                            guestGrubConf.parseConf(guest_grub_conf)
                            for entry in guestGrubConf.entries:
                                # if entry has kernel value we can use it in our grub.conf
                                # some distros uses uuid instead of root
                                if entry.getCommand("kernel"):
                                    entry.title = entry.title + " [ %s ]" % p.getName()

                                    # if device order changed we should update device order in foreign grub.conf
                                    _grub_dev = yali.bootloader.findGrubDev(p.getPath())

                                    if entry.getCommand("root"):
                                        # update device order for root command
                                        _root = entry.getCommand("root")
                                        if _root.value != '':
                                            _root.value = _update_dev(_root.value, _grub_dev)

                                        # update device order for kernel command if already defined
                                        _kernel = entry.getCommand("kernel")
                                        if _kernel and _root.value:
                                            if _kernel.value.startswith('('):
                                                _kernel.value = ''.join([_root.value, _kernel.value.split(')')[1]])

                                        # update device order for initrd command if already defined
                                        _initrd = entry.getCommand("initrd")
                                        if _initrd and _root.value:
                                            if _initrd.value.startswith('('):
                                                _initrd.value = ''.join([_root.value, _initrd.value.split(')')[1]])

                                    grubConf.addEntry(entry)
                        else:
                            # If not a proper grub.conf found umount the partition
                            yali.sysutils.umount_()

        # write the new grub.conf
        grubConf.write(grubConfPath)

        # BUG:#11255 normal user doesn't mount /mnt/archive directory. 
        # We set new formatted partition priveleges as user=root group=disk and change mod as 0770
        # Check archive partition type
        archiveRequest = partrequests.searchPartTypeAndReqType(parttype.archive, request.mountRequestType)
        if archiveRequest:
            ctx.debugger.log("Archive type request found!")
            yali.postinstall.setPartitionPrivileges(archiveRequest, 0770, 0, 6)

        # Umount system paths
        yali.sysutils.umountSystemPaths()

        # GPT stuff
        gptsync_path = yali.sysutils.find_executable("gptsync")
        if gptsync_path and not pardusPart:
            gptsync = os.popen("%s %s" % (gptsync_path, root_part_req.partition().getDevicePath()))
            for line in gptsync.readlines():
                if line.startswith("Status:"):
                    ctx.debugger.log("GPTSYNC: %s" % line.split("Status: ")[1])
            gptsync.close()
            time.sleep(1)
        else:
            ctx.debugger.log("GPTSYNC: Command Not Found !")

        # finally install it
        return loader.installGrub(ctx.installData.bootLoaderDev, _ins_part)

    def showError(self, title, message, parent=None):
        r = ErrorWidget(parent)
        r.label.setText(message)
        d = Dialog(title, r, self, closeButton=False)
        d.resize(300,200)
        d.exec_()

class ErrorWidget(QtGui.QWidget):

    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)

        self.gridlayout = QtGui.QGridLayout(self)
        self.vboxlayout = QtGui.QVBoxLayout()

        self.label = QtGui.QLabel(self)
        self.vboxlayout.addWidget(self.label)

        self.hboxlayout = QtGui.QHBoxLayout()

        spacerItem = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem)

        self.reboot = QtGui.QPushButton(self)
        self.reboot.setFocusPolicy(Qt.NoFocus)
        self.reboot.setText(_("Reboot"))

        self.hboxlayout.addWidget(self.reboot)
        self.vboxlayout.addLayout(self.hboxlayout)
        self.gridlayout.addLayout(self.vboxlayout,0,0,1,1)

        yali.sysutils.ejectCdrom()

        self.connect(self.reboot, SIGNAL("clicked()"),self.slotReboot)

    def slotReboot(self):
        yali.sysutils.reboot()

