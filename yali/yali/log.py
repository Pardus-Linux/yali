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

# Log module which can log/write various information to different
# places (log file, tty...)

from yali.constants import consts

class Logger:

    def __init__(self, target_list):
        
        self._targets = []
        for t in target_list:
            self._targets.append(open(t, "a"))

    def write(self, s):
        if not self._targets:
            return

        for t in self._targets:
            t.write(s)
            t.flush()

    def close(self):
        if not self._targets:
            return

        for t in self._targets:
            t.close()


# default logger
logger = Logger([consts.log_file, "/dev/tty10"])
