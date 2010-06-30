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
import glob
import time

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

from yali.exception import *
from yali.constants import consts
import yali.sysutils
import yali.partitiontype as parttype
import yali.partitionrequest as request
from yali.partitionrequest import partrequests
import yali.gui.context as ctx
from pardus.sysutils import get_kernel_option

grub_conf_tmp = """\
default 0
timeout 10
gfxmenu /boot/grub/message
background 10333C

title %(pardus_version)s
root (%(grub_root)s)
kernel (%(grub_root)s)/boot/%(boot_kernel)s %(boot_parameters)s
initrd (%(grub_root)s)/boot/%(initramfs)s

"""

win_part_tmp = """
title %(title)s (%(fs)s) - %(root)s
rootnoverify (%(grub_root)s)
makeactive
chainloader +1

"""

win_part_tmp_multiple_disks = """
title %(title)s (%(fs)s) - %(root)s
map (hd0) (%(grub_dev)s)
map (%(grub_dev)s) (hd0)
rootnoverify (%(grub_root)s)
makeactive
chainloader +1

"""

def findGrubDev(dev_path, device_map=None):
    """ Returns the GRUB device from given dev_path
        It uses YALI's deviceMap created from EDD"""
    if not device_map:
        device_map = os.path.join(consts.target_dir, "boot/grub/device.map")
    if dev_path.find("cciss") > 0:
        # HP Smart array controller (something like /dev/cciss/c0d0p1)
        dev_name = os.path.basename(dev_path)[:-2]
    else:
        dev_name = str(filter(lambda u: u.isalpha(),
                              os.path.basename(dev_path)))

    ctx.debugger.log("dev_path:%s" % dev_path)
    ctx.debugger.log("dev_name:%s" % dev_name)

    for l in open(device_map).readlines():
        if l.find(dev_name) >= 0:
            l = l.split()
            d = l[0]
            # remove paranthesis
            return d[1:-1]
    return ''

def getMinor(dev_path):
    return str(int(filter(lambda d: d.isdigit(), dev_path)) -1)

class BootLoader:
    """ Bootloader Operations 
        Default bootlader is GRUB """
    def __init__(self):
        self.device_map = os.path.join(consts.target_dir, "boot/grub/device.map")
        self.grub_conf = os.path.join(consts.target_dir, "boot/grub/grub.conf")

    def _find_hd0(self):
        """ Returns first disk from deviceMap """
        for l in open(self.device_map).readlines():
            if l.find("hd0") >= 0:
                l = l.split()
                # (hd0)   /dev/hda
                d = l[1]
                return d

    def writeGrubConf(self, install_root_path, install_dev, install_root_path_label):
        """ Check configurations and write grub.conf to the installed system.
            Default path is /mnt/target/boot/grub.conf """
        if not install_dev.startswith("/dev/"):
            install_dev = "/dev/%s" % install_dev

        # some paths has own directories like (/dev/cciss/c0d0p1)
        # it removes /dev/ and gets the device.
        install_root = install_root_path[5:]
        ctx.debugger.log("WGC: Given install_root_path is : %s" % install_root_path)
        ctx.debugger.log("WGC: Final install_root is : %s" % install_root)

        grub_dir = os.path.join(consts.target_dir, "boot/grub")
        if not os.path.exists(grub_dir):
            os.makedirs(grub_dir)

        # write an empty grub.conf, for grub to create a device map.
        open(self.grub_conf, "w").close()
        deviceMap = open(self.device_map, "w")
        i = 0

        #opts = get_kernel_option("mudur")
        opts = yali.sysutils.liveMediaSystem()
        if opts.__eq__("harddisk"):
            diskList = ctx.installData.orderedDiskList[1:]
        else:
            diskList = ctx.installData.orderedDiskList

        # if install root is equal with grub root
        # force install root to be hd0
        if install_root.startswith(ctx.installData.bootLoaderDev):
            # create device map
            if opts.__eq__("harddisk"):
                ctx.installData.orderedDiskList = ctx.installData.orderedDiskList[1:]
            for disk in ctx.installData.orderedDiskList:
                if install_root.startswith(disk[5:]):
                    deviceMap.write("(hd%d)\t%s\n" % (i,disk))
                    diskList.remove(disk)
                    i+=1

        # create device map
        for disk in diskList:
            deviceMap.write("(hd%d)\t%s\n" % (i,disk))
            i+=1
        deviceMap.close()

        # cmd = "/sbin/grub --batch --no-floppy --device-map=%s < %s" % (self.device_map, self.grub_conf)
        # os.system(cmd)

        major = findGrubDev(install_root_path)

        # grub_root is the device on which we install.
        minor = getMinor(install_root)
        grub_root = ",".join([major, minor])

        def find_pardus_release():
            """Returns Pardus Relase"""
            releaseConfPath = os.path.join(consts.target_dir, "etc/pardus-release")
            ctx.debugger.log("DEBUG: Pardus Release %s" % file(releaseConfPath).readlines()[0].strip())
            return file(releaseConfPath).readlines()[0].strip()

        def find_boot_kernel():
            """ Returns the installed kernel version """
            d = os.path.join(consts.target_dir, "boot")
            k = glob.glob(d + "/kernel-*")
            return os.path.basename(sorted(k)[-1])

        def find_initramfs_name(bk):
            """ Returns the installed initramfs name """
            ver = bk[len("kernel-"):]
            return "initramfs-%s" % ver

        def boot_parameters(root_label):
            """ Returns kernel parameters from cmd_line.
                It also cleans unnecessary options """

            def is_required(param):
                params = ["root","initrd","init","xorg","yali","BOOT_IMAGE","lang","mudur",consts.kahya_param]
                for p in params:
                    if param.startswith("%s=" % p):
                        return False
                return True

            s = []
            # Add initramfs.conf config file support on 2009.1. But may be old system didnt have it(Like Pardus 2008)
            #if not os.path.exists(os.path.join(consts.target_dir, "etc/initramfs.conf")):
            # Removing root=LABEL= from cmdline makes problem for suspend
            s.append("root=LABEL=%s" % (root_label))
            # a hack for http://bugs.pardus.org.tr/3345
            rt = request.mountRequestType
            pt = parttype.swap
            swap_part_req = partrequests.searchPartTypeAndReqType(pt, rt)
            if swap_part_req:
                s.append("resume=%s" %(swap_part_req.partition().getPath()))

            # Get parameters from cmdline.
            for i in [x for x in open("/proc/cmdline", "r").read().split()]:
                if is_required(i):
                    s.append(i)

            return " ".join(s).strip()

        boot_kernel = find_boot_kernel()
        ctx.debugger.log("FBK: Kernel found as %s" % boot_kernel)
        initramfs_name = find_initramfs_name(boot_kernel)
        boot_parameters =  boot_parameters(install_root_path_label)
        s = grub_conf_tmp % {"root": install_root,
                             "grub_root": grub_root,
                             "pardus_version": find_pardus_release(),
                             "boot_kernel": boot_kernel,
                             "boot_parameters": boot_parameters,
                             "initramfs": initramfs_name}
        open(self.grub_conf, "w").write(s)

    def grubConfAppendWin(self, install_dev, win_dev, win_root, win_fs):
        """ Appends Windows Partitions to the GRUB Conf """
        grub_dev = findGrubDev(win_dev)
        minor = getMinor(win_root)
        grub_root = ",".join([grub_dev, minor])

        ctx.debugger.log("GCAW : win_dev : %s , win_root : %s " % (win_dev, win_root))
        ctx.debugger.log("GCAW : grub_dev: %s , grub_root: %s " % (grub_dev, grub_root))
        ctx.debugger.log("GCAW : install_dev: %s " % install_dev)

        if not install_dev:
            install_dev = self._find_hd0()

        ctx.debugger.log("GCAW :2install_dev: %s " % install_dev)

        dev_str = str(os.path.basename(install_dev))
        ctx.debugger.log("GCAW : dev_str: %s " % dev_str)

        if win_dev == dev_str:
            s = win_part_tmp % {"title": _("Windows"),
                                "grub_root": grub_root,
                                "root": win_root,
                                "fs": win_fs}
        else:
            s = win_part_tmp_multiple_disks % {"title": _("Windows"),
                                               "grub_root": grub_root,
                                               "grub_dev": grub_dev,
                                               "root": win_root,
                                               "fs": win_fs}

        open(self.grub_conf, "a").write(s)

    def installGrub(self, grub_install_root=None, root_path=None):
        """ Install GRUB to the given device or partition """

        major = findGrubDev(root_path)
        minor = getMinor(root_path)
        # LiveDisk installation grub detects usb
        #opts = get_kernel_option("mudur")
        opts = yali.sysutils.liveMediaSystem()
        ctx.debugger.log("IG: I have found mediaSystem '%s'" % opts)
        ctx.debugger.log("IG: I have found major:'%s' minor:'%s'" % (major, minor))

        if opts.__eq__("harddisk"):
            major = major.replace(major[2],chr(ord(major[2])+1))

        root_path = "(%s,%s)" % (major, minor)

        if not grub_install_root.startswith("/dev/"):
            grub_install_root = "/dev/%s" % grub_install_root

        # LiveDisk installation grub detects usb
        major = findGrubDev(grub_install_root)
        if opts.__eq__("harddisk"):
            major = major.replace(major[2],chr(ord(major[2])+1))

        ctx.debugger.log("IG: I have found major as '%s'" % major)
        if ctx.installData.bootLoaderOption == 1:
            # means it will install to a partition not MBR
            minor = getMinor(grub_install_root)
            setupto = "(%s,%s)" % (major, minor)
        else:
            # means it will install to the MBR
            setupto = "(%s)" % major
        ctx.debugger.log("IG: And the last it will install to '%s'" % setupto)

        batch_template = """root %s
setup %s
quit
""" % (root_path, setupto)

        file('/tmp/_grub','w').write(batch_template)
        ctx.debugger.log("IG: Batch content : %s" % batch_template)
        cmd = "%s --no-floppy --batch < /tmp/_grub" % yali.sysutils.find_executable("grub")
        #cmd = "%s --batch --no-floppy --device-map=%s < %s" % (yali.sysutils.find_executable("grub"), self.device_map, self.grub_conf)

        ctx.debugger.log("IG: Chrooted jobs are finalizing.. ")
        # before installing the bootloader we have to finish chrooted jobs..
        yali.sysutils.finalizeChroot()

        ctx.debugger.log("IG: Grub install cmd is %s" % cmd)
        if os.system(cmd) > 0:
            ctx.debugger.log("grub")
            ctx.debugger.log("IG: Command failed %s - trying again.. " % cmd)
            time.sleep(2)
            if os.system(cmd) > 0:
                raise YaliException, "Command failed: %s" % cmd
            else:
                if os.system("sync") > 0:
                    return False
                else:
                    return True
            return False
        else:
            if os.system("sync") > 0:
                return False
            else:
                return True

