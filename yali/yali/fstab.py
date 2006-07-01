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

from os.path import join

from yali.constants import consts

class FstabEntry:
    def __init__(self, dev, mp, fs, opts, d="0", p="0"):
        self.device = dev
        if mp:
            self.mountpoint = mp
        else:
            self.mountpoint = "none"
        self.filesystem = fs
        self.options = opts
        self.d = d
        self.p = p
    
standard_entries = [
    FstabEntry("/dev/fd0", "/media/floopy", "auto", "noauto,user,sync")]
    FstabEntry("none", "/proc", "proc", "defaults"),
    FstabEntry("none", "/dev/shm", "tmpfs", "defaults")]

class Fstab(file):
    
    _path = join(consts.target_dir, "etc/fstab")

    def __init__(self):
        file.__init__(self, self._path, "w")


    def insert(self, e):
        l = "%s\t%s\t%s\t%s\t%s %s\n" % (
            e.device, e.mountpoint, e.filesystem,
            e.options, e.d, e.p)
        self.write(l)

    def close(self):
        for e in standard_entries:
            self.insert(e)
        file.close(self)

