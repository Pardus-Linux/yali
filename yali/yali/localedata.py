# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2007, TUBITAK/UEKAE
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



class Keymap:
    def __init__(self, console, X, translation):
        self.console = console
        self.X = X
        self.translation = translation

##
# There are some locales (Turkish, for instance) that provide more
# than one keyboard.
class MultiKeymap:
    def __init__(self, keymaps):
        self.keymaps = keymaps

    def getAllKeyboards(self):
        return [k.keyboard for k in self.keymaps]

    def getAllTranslations(self):
        return [k.translation for k in self.keymaps]

    def getTranslation(self, keyboard):
        for keymap in self.keymaps:
            if keymap.keyboard == keyboard:
                return keymap.translation
        return None


def getSupportedLanguages():
    global locales

    supported = []
    for lang in locales.keys():
        if locales[lang]["isSupported"]:
            supported.append(lang)
    return supported


def getKeymaps():
    global locales

    keys = []
    for lang in locales.keys():
        keymap = locales[lang]["keymap"]
        if isinstance(keymap, MultiKeymap):
            keys.extend(keymap.keymaps)
        elif isinstance(keymap, Keymap):
            keys.append(keymap)
    return keys


def getLangsWithKeymaps():
    global locales

    # FIXME: code duplication
    keys = []
    for lang in locales.keys():
        keymap = locales[lang]["keymap"]
        if isinstance(keymap, MultiKeymap):
            keys.append( (lang, keymap.keymaps) )
        elif isinstance(keymap, Keymap):
            keys.append( (lang, keymap) )
    return keys


locales = {
    "af" : {
        "isSupported" : False,
        "name" : _("Afrikaans"),
        "keymap" : Keymap("us", "us", _("Afrikaans")),
        "locale" : "af_ZA.UTF-8",
        "consolefont" : None,
        "consoletranslation" : None
        },

    "ar" : {
        "isSupported" : False,
        "name" : _("Arabic"),
        "keymap" : Keymap("us", "ara", _("Arabic")),
        "locale" : "ar_SA.UTF-8",
        "consolefont" : None,
        "consoletranslation" : None
        },

    "be" : {
        "isSupported" : False,
        "name" : _("Belgium"),
        "keymap" : Keymap("be-latin1", "be", _("Belgium")),
        "locale" : "be_BY.UTF-8",
        "consolefont" : None,
        "consoletranslation" : None
        },

    "bg" : {
        "isSupported" : False,
        "name" : _("Bulgarian"),
        "keymap" : Keymap("bg", "bg", _("Bulgarian")),
        "locale" : "bg_BG.UTF-8",
        "consolefont" : None,
        "consoletranslation" : None
        },

    "ca" : {
        "isSupported" : False,
        "name" : _("Catalan"),
        "keymap" : Keymap("es", "es", _("Catalan")),
        "locale" : "ca_ES.UTF-8",
        "consolefont" : None,
        "consoletranslation" : None
        },

    "hr" : {
        "isSupported" : False,
        "name" : _("Croatian"),
        "keymap" : Keymap("croat", "hr", _("Croatian")),
        "locale" : "hr_HR.UTF-8",
        "consolefont" : None,
        "consoletranslation" : None
        },

    "cz" : {
        "isSupported" : False,
        "name" : _("Czech"),
        "keymap" : Keymap("cz-lat2", "cz", _("Czech")),
        "locale" : "cs_CZ.UTF-8",
        "consolefont" : None,
        "consoletranslation" : None
        },

    "da" : {
        "isSupported" : False,
        "name" : _("Danish"),
        "keymap" : Keymap("dk", "dk", _("Danish")),
        "locale" : "da_DK.UTF-8",
        "consolefont" : None,
        "consoletranslation" : None
        },

    "nl" : {
        "isSupported" : True,
        "name" : _("Dutch"),
#bug #4271
#        "keymap" : Keymap("nl", "nl", _("Dutch")),
        "keymap" : Keymap("us", "us", _("Dutch (US)")),
        "locale" : "nl_NL.UTF-8",
        "consolefont" : "iso01.16",
        "consoletranslation" : "8859-1"
        },

    "en" : {
        "isSupported" : True,
        "name" : _("English"),
        "keymap" : Keymap("us", "us", _("English")),
        "locale" : "en_US.UTF-8",
        "consolefont" : "iso01.16",
        "consoletranslation" : "8859-1"
        },

    "et" : {
        "isSupported" : False,
        "name" : _("Estonian"),
        "keymap" : Keymap("et", "ee", _("Estonian")),
        "locale" : "et_EE.UTF-8",
        "consolefont" : None,
        "consoletranslation" : None
        },

    "fi" : {
        "isSupported" : False,
        "name" : _("Finnish"),
        "keymap" : Keymap("fi", "fi", _("Finnish")),
        "locale" : "fi_FI.UTF-8",
        "consolefont" : None,
        "consoletranslation" : None
        },

    "fr" : {
        "isSupported" : False,
        "name" : _("French"),
        "keymap" : Keymap("fr-latin1", "fr", _("French")),
        "locale" : "fr_FR.UTF-8",
        "consolefont" : None,
        "consoletranslation" : None
        },

    "de" : {
        "isSupported" : True,
        "name" : _("German"),
        "keymap" : Keymap("de-latin1-nodeadkeys", "de", _("German")),
        "locale" : "de_DE.UTF-8",
        "consolefont" : "iso01.16",
        "consoletranslation" : "8859-1"
        },

    "gr" : {
        "isSupported" : False,
        "name" : _("Greek"),
        "keymap" : Keymap("gr", "gr", _("Greek")),
        "locale" : "el_GR.UTF-8",
        "consolefont" : None,
        "consoletranslation" : None
        },

    "hu" : {
        "isSupported" : False,
        "name" : _("Hungarian"),
        "keymap" : Keymap("hu", "hu", _("Hungarian")),
        "locale" : "hu_HU.UTF-8",
        "consolefont" : None,
        "consoletranslation" : None
        },

    "is" : {
        "isSupported" : False,
        "name" : _("Icelandic"),
        "keymap" : Keymap("is-latin1", "is", _("Icelandic")),
        "locale" : "is_IS.UTF-8",
        "consolefont" : None,
        "consoletranslation" : None
        },

    "it" : {
        "isSupported" : False,
        "name" : _("Italian"),
        "keymap" : Keymap("it", "it", _("Italian")),
        "locale" : "it_IT.UTF-8",
        "consolefont" : None,
        "consoletranslation" : None
        },

    "ja" : {
        "isSupported" : False,
        "name" : _("Japanese"),
        "keymap" : Keymap("jp106", "jp", _("Japanese")),
        "locale" : "ja_JP.UTF-8",
        "consolefont" : None,
        "consoletranslation" : None
        },

    "mk" : {
        "isSupported" : False,
        "name" : _("Macedonian"),
        "keymap" : Keymap("mk", "mkd", _("Macedonian")),
        "locale" : "mk_MK.UTF-8",
        "consolefont" : None,
        "consoletranslation" : None
        },

    "ml" : {
        "isSupported" : False,
        "name" : _("Malayalam"),
        "keymap" : Keymap("us", "us", _("Malayalam")),
        "locale" : "ml_IN.UTF-8",
        "consolefont" : None,
        "consoletranslation" : None
        },

    "nb" : {
        "isSupported" : False,
        "name" : _("Norwegian"),
        "keymap" : Keymap("no", "no", _("Norwegian")),
        "locale" : "nb_NO.UTF-8",
        "consolefont" : None,
        "consoletranslation" : None
        },

    "pl" : {
        "isSupported" : False,
        "name" : _("Polish"),
        "keymap" : Keymap("pl2", "pl", _("Polish")),
        "locale" : "pl_PL.UTF-8",
        "consolefont" : None,
        "consoletranslation" : None
        },

    "pt" : {
        "isSupported" : False,
        "name" : _("Portuguese"),
        "keymap" : Keymap("pt-latin1", "pt", _("Portuguese")),
        "locale" : "pt_PT.UTF-8",
        "consolefont" : None,
        "consoletranslation" : None
        },

    "br" : {
        "isSupported" : True,
        "name" : _("Brazilian"),
        "keymap" : Keymap("br-abnt2", "br", _("Brazilian")),
        "locale" : "pt_BR.UTF-8",
        "consolefont" : None,
        "consoletranslation" : None
        },

    "ru" : {
        "isSupported" : False,
        "name" : _("Russian"),
        "keymap" : Keymap("ru", "ru", _("Russian")),
        "locale" : "ru_RU.UTF-8",
        "consolefont" : None,
        "consoletranslation" : None
        },

    "sr" : {
        "isSupported" : False,
        "name" : _("Serbian"),
        "keymap" : Keymap("sr-cy", "srp", _("Serbian")),
        "locale" : "sr_CS.UTF-8",
        "consolefont" : None,
        "consoletranslation" : None
        },

    "sk" : {
        "isSupported" : False,
        "name" : _("Slovak"),
        "keymap" : Keymap("sk-qwerty", "sk", _("Slovak")),
        "locale" : "sk_SK.UTF-8",
        "consolefont" : None,
        "consoletranslation" : None
        },

    "sl" : {
        "isSupported" : False,
        "name" : _("Slovenian"),
        "keymap" : Keymap("slovene", "si", _("Slovenian")),
        "locale" : "sl_SI.UTF-8",
        "consolefont" : None,
        "consoletranslation" : None
        },

    "es" : {
        "isSupported" : False,
        "name" : _("Spanish"),
        "keymap" : Keymap("es", "es", _("Spanish")),
        "locale" : "es_ES.UTF-8",
        "consolefont" : None,
        "consoletranslation" : None
        },

    "sv" : {
        "isSupported" : False,
        "name" : _("Swedish"),
        "keymap" : Keymap("sv-latin1", "se", _("Swedish")),
        "locale" : "sv_SE.UTF-8",
        "consolefont" : None,
        "consoletranslation" : None
        },

    "tr" : {
        "isSupported" : True,
        "name" : _("Turkish"),
        "keymap" : MultiKeymap([Keymap("trq", "trq", _("Turkish Q")),
                                Keymap("trf", "trf", _("Turkish F"))]),
        "locale" : "tr_TR.UTF-8",
        "consolefont" : "iso09.16",
        "consoletranslation" : "8859-9"
        },

    "uk" : {
        "isSupported" : False,
        "name" : _("Ukrainian"),
        "keymap" : Keymap("ua-utf", "ua", _("Ukrainian")),
        "locale" : "uk_UA.UTF-8",
        "consolefont" : None,
        "consoletranslation" : None
        },

    "vi" : {
        "isSupported" : False,
        "name" : _("Vietnamese"),
        "keymap" : Keymap("us", "vn", _("Vietnamese")),
        "locale" : "vi_VN.UTF-8",
        "consolefont" : None,
        "consoletranslation" : None
        },

    "cy" : {
        "isSupported" : False,
        "name" : _("Welsh"),
        "keymap" : Keymap("uk", "gb", _("English (GB)")),
        "locale" : "cy_GB.UTF-8",
        "consolefont" : None,
        "consoletranslation" : None
        },

    }
