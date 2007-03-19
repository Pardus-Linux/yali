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

import os
import glob

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext


from yali.exception import *
from yali.constants import consts
import yali.sysutils
import yali.partitiontype as parttype
import yali.partitionrequest as request
from yali.partitionrequest import partrequests


grub_conf_tmp = """\
default 0
timeout 10
splashimage = (%(grub_root)s)/boot/grub/splash.xpm.gz
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
map (hd0) (hd1)
map (hd1) (hd0)
rootnoverify (%(grub_root)s)
makeactive
chainloader +1

"""


class BootLoader:
    def __init__(self):
        self.device_map = os.path.join(consts.target_dir, "boot/grub/device.map")
        self.grub_conf = os.path.join(consts.target_dir, "boot/grub/grub.conf")
        self.install_root = ""
        self.install_dev = ""

        self.win_dev = ""
        self.win_root = ""
        self.win_fs = ""

    def _find_grub_dev(self, dev):
        dev_name = str(filter(lambda u: u.isalpha(), dev))
        for l in open(self.device_map).readlines():
            if l.find(dev_name) >= 0:
                l = l.split()
                d = l[0]
                # remove paranthesis
                return d[1:-1]

    def write_grub_conf(self):
        grub_dir = os.path.join(consts.target_dir, "boot/grub")
        if not os.path.exists(grub_dir):
            os.makedirs(grub_dir)
    
        #write an empty grub.conf, for grub to create a device map.
        open(self.grub_conf, "w").close()
        # create device map
        cmd = "/sbin/grub --batch --no-floppy --device-map=%s < %s" % \
                                (self.device_map, self.grub_conf)
        os.system(cmd)

        minor = str(int(filter(lambda u: u.isdigit(), self.install_root)) -1)
        # grub_root is the device on which we install.
        # grub_root = ",".join([self._find_grub_dev(self.install_root),
        #                      minor])
        ####
        # grub_root is always hd0 (http://liste.pardus.org.tr/gelistirici/2007-March/005725.html)
        grub_root = ",".join(["hd0", minor])

        def find_boot_kernel():
            d = os.path.join(consts.target_dir, "boot")
            k = glob.glob(d + "/kernel-*")
            return os.path.basename(k[0])
        
        def find_initramfs_name(bk):
            ver = bk[len("kernel-"):]
            return "initramfs-%s" % ver
    
        def boot_parameters(root):
            s = []

            # Get parameters from cmdline.
            for i in [x for x in open("/proc/cmdline", "r").read().split() if not x.startswith("init=") and not x.startswith("xorg=")]:
                if i.startswith("root="):
                    s.append("root=/dev/%s" % (root))
                elif i.startswith("mudur="):
                    mudur = "mudur="
                    for p in i[len("mudur="):].split(','):
                        if p == "livecd" or p == "livedisk": continue
                        mudur += p
                    if not len(mudur) == len("mudur="):
                        s.append(mudur)
                else:
                    s.append(i)

            # a hack for http://bugs.pardus.org.tr/3345
            rt = request.mountRequestType
            pt = parttype.swap
            swap_part_req = partrequests.searchPartTypeAndReqType(pt, rt)
            if swap_part_req:
                s.append("resume=%s" %(swap_part_req.partition().getPath()))


            return " ".join(s).strip()

            

 
        boot_kernel = find_boot_kernel()
        initramfs_name = find_initramfs_name(boot_kernel)
        boot_parameters =  boot_parameters(self.install_root)
        s = grub_conf_tmp % {"root": self.install_root,
                             "grub_root": grub_root,
                             "pardus_version": consts.pardus_version,
                             "boot_kernel": boot_kernel,
                             "boot_parameters": boot_parameters,
                             "initramfs": initramfs_name}
        open(self.grub_conf, "w").write(s)



    def grub_conf_append_win(self):
        grub_dev = self._find_grub_dev(self.win_dev)
        minor = str(int(filter(lambda u: u.isdigit(), self.win_root)) -1)
        grub_root = ",".join([grub_dev, minor])


        dev_str = str(filter(lambda u: u.isalpha(), self.install_dev))
        if self.win_dev == dev_str:
            s = win_part_tmp % {"title": _("Windows"),
                                "grub_root": grub_root,
                                "root": self.win_root,
                                "fs": self.win_fs}
        else:
            s = win_part_tmp_multiple_disks % {"title": _("Windows"),
                                               "grub_root": grub_root,
                                               "root": self.win_root,
                                               "fs": self.win_fs}
    
        open(self.grub_conf, "a").write(s)
        
    
    
    def install_grub(self):
        cmd = "%s --root-directory=%s %s" % (yali.sysutils.find_executable("grub-install"),
                                             consts.target_dir,
                                             os.path.join("/dev", self.install_dev))
        if os.system(cmd) != 0:
            raise YaliException, "Command failed: %s" % cmd

