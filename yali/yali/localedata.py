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

from yali.constants import consts

# TODO: merge keybords with this module!


localedata = {
    "tr" : {
        "locale": "tr_TR.UTF-8",
        "consolefont" : "iso09.16",
        "consoletranslation" : "8859-9"
        },

    "en" : {
        "locale": "en_US.UTF-8",
        "consolefont" : "iso01.16",
        "consoletranslation" : "8859-1"
        },

    "nl" : {
        "locale": "nl_NL.UTF-8",
        "consolefont" : "iso01.16",
        "consoletranslation" : "8859-1"
        },

    "de" : {
	"locale": "de_DE.UTF-8",
	"consolefont" : "iso01.16",
	"consoletranslation" : "8859-1"
	}
    }


def write_locale_from_cmdline():
    locale_file_path = os.path.join(consts.target_dir, "etc/env.d/03locale")
    f = open(locale_file_path, "w")

    f.write("LANG=%s\n" % localedata[consts.lang]["locale"])
    f.write("LC_ALL=%s\n" % localedata[consts.lang]["locale"])


def write_font_from_cmdline(keydata):
    lines = []

    lang = "tr"
    # Worst code ever, this depends on keyboard module.
    # will fix it later on...
    keymap = keydata["keymap"]
    if keymap in ("us"):
        lang = "en"

    consolefont_file_path = os.path.join(consts.target_dir,
                                         "etc/conf.d/consolefont")

    for l in open(consolefont_file_path, "r").readlines():
        if l.strip().startswith("CONSOLEFONT="):
            l = "CONSOLEFONT=%s\n" % localedata[lang]["consolefont"]
        elif l.strip().startswith("CONSOLETRANSLATION="):
            l = "CONSOLETRANSLATION=%s\n" % localedata[lang]["consoletranslation"]
        lines.append(l)

    open(consolefont_file_path, "w").writelines(lines)
    

    
