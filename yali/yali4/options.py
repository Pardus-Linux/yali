# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2009, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

# YALI options module defines a class for command line options.

from optparse import OptionParser

class Options(object):

    def __init__(self):
        parser = OptionParser()
        parser.add_option("-d", "--debug", dest="debug",
                          action="store_true", default="True",
                          help="enable debug")
        parser.add_option("-q", "--dryRun", dest="dryRun",
                          action="store_true", default="False",
                          help="only show the result")
        parser.add_option("-f", "--firstBoot", dest="firstBoot",
                          action="store_true", default="False",
                          help="start with first boot options")
        parser.add_option("-r", "--rescue", dest="rescueMode",
                          action="store_true", default="False",
                          help="start Yali with rescue mode")
        parser.add_option("-k", "--kahyaFile", dest="kahyaFile",
                          help="run with Kahya file", metavar="FILE")
        parser.add_option("-K", "--useKahyaDefault", dest="useKahya",
                          action="store_true", default="False",
                          help="start kahya with default.xml")
        parser.add_option("-s", "--startFrom", dest="startupScreen",
                          help="start from the given screen (num)", type="int", default=0)
        parser.add_option("-p", "--plugin", dest="plugin",
                          help="load given plugin", type="str", default=None)
        parser.add_option("-t", "--theme", dest="theme",
                          help="load given theme", type="str", default="2009")
        self.options, self.args = parser.parse_args()

    def __getattr__(self, name):
        if hasattr(self.options, name):
            return getattr(self.options, name)
        else:
            return None

# Command line options singleton.
options = Options()
