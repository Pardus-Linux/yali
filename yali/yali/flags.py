#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
from pardus.sysutils import get_kernel_option

class Flags:

    def __getattr__(self, attr):
        if self.__dict__['flags'].has_key(attr):
            return self.__dict__['flags'][attr]
        raise AttributeError, attr

    def __setattr__(self, attr, val):
        if self.__dict__['flags'].has_key(attr):
            self.__dict__['flags'][attr] = val
        else:
            raise AttributeError, attr

    def get(self, attr, val=None):
        if self.__dict__['flags'].has_key(attr):
            return self.__dict__['flags'][attr]
        else:
            return val

    def parse_kernel_options(self):
        """Parse yali= from kernel boot parameters."""

        options = get_kernel_option("yali")
        self.__dict__['flags']['live'] = options.has_key("live") or \
                                         os.path.exists("/var/run/pardus/livemedia")
        if options.has_key("system"):
            self.__dict__['flags']['install_type'] = 1
        elif options.has_key("oem") :
            self.__dict__['flags']['install_type'] = 2
        elif options.has_key("firstboot"):
            self.__dict__['flags']['install_type'] = 3
        elif options.has_key("rescue") :
            self.__dict__['flags']['install_type'] = 4
        elif options.has_key("default") :
            self.__dict__['flags']['install_type'] = 0

        if options.has_key("theme"):
            self.__dict__['flags']['theme'] = options["theme"]

        if options.has_key("branding"):
            self.__dict__['flags']['branding'] = options["branding"]

        self.__dict__['flags']['kahya'] = options.has_key("kahyaFile") or \
                                          os.path.exists("/usr/share/yali/data/default.xml")

        if options.has_key("nolvm"):
            self.__dict__['flags']['partitioning_lvm'] = False

        if options.has_key("collection"):
            self.__dict__['flags']['collection'] = True

        for key in [_key for _key in options.keys() \
                    if _key not in ("live", "system", "firstboot", "oem", "firstboot", "rescue", "theme")]:
            self.__dict__[key] = options[key] if options[key] else True

    def __init__(self):
        self.__dict__['flags'] = {}
        self.__dict__['flags']['debug'] = False
        self.__dict__['flags']['install_type'] = 0
        self.__dict__['flags']['partitioning_lvm'] = True
        self.__dict__['flags']['collection'] = False
        self.__dict__['flags']['baseonly'] = False
        self.__dict__['flags']['kahya'] = False
        self.__dict__['flags']['kahyaFile'] = ""
        self.__dict__['flags']['live'] = False
        self.__dict__['flags']['dmraid'] = True
        self.__dict__['flags']['dryRun'] = False
        self.__dict__['flags']['startup'] = 0
        self.__dict__['flags']['theme'] = ""
        self.__dict__['flags']['branding'] = ""
