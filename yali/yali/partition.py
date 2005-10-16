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


##
# Class representing a single partition within a Device object
class Partition:

    def __init__(self, device, part, minor, mb, start, end, fs_type):
        self._device = device
        self._parted_part = part
        self._minor = minor
        self._mb = mb
        self._start = start
        self._end = end
        self._fstype = fs_type or "unknown"

    def get_minor(self):
        return self._minor

    def get_fsType(self):
        return self._fstype

    def get_start(self):
        return self._start

    def get_end(self):
        return self._end

    def get_mb(self):
        return self._mb

    def get_gb(self):
        return self._mb / 1024.0
