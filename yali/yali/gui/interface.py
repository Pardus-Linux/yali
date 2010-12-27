#!/usr/bin/python
# -*- coding: utf-8 -*-

import gettext
_ = gettext.translation('yali', fallback=True).ugettext

import yali.context as ctx
from yali.gui.YaliDialog import MessageWindow, InformationWindow, ProgressWindow, ExceptionWindow

class Interface(object):
    def __init__(self):
        self._informationWindow = None
        self._warnedUnusedRaidMembers = []
        self._initLabelAnswers = {}
        self._inconsistentLVMAnswers = {}

    @property
    def informationWindow(self):
        if not self._informationWindow:
            self._informationWindow = InformationWindow()
        return self._informationWindow

    def exceptionWindow(self, error, traceback):
        return ExceptionWindow(error, traceback).rc

    def progressWindow(self, message):
        return ProgressWindow(message)

    def messageWindow(self, title, text, type="ok", default=None, customButtons=None, customIcon=None):
        return MessageWindow(title, text, type, default, customButtons, customIcon, run=True).rc

    def detailedMessageWindow(self, title, text, longText, type="ok", default=None, customButtons=None, customIcon=None):
        return MessageWindow(title, text, type, default, customButtons, customIcon, run=True, detailed=True, longText=longText).rc

    def unusedRaidMembers(self, unusedRaidMembers):
        """Warn about unused BIOS RAID members"""
        unusedRaidMembers = filter(lambda m: m not in self._warnedUnusedRaidMembers, unusedRaidMembers)
        if unusedRaidMembers:
            self._warnedUnusedRaidMembers.extend(unusedRaidMembers)
            unusedRaidMembers.sort()
            self.messageWindow(_("Warning"),
                               _("Disk contains %(members_count)s BIOS RAID metadata, but is not part of "
                                 "any recognized BIOS RAID sets. Ignoring disk %(members)s.")
                                 % {"members_count":len(unusedRaidMembers), "members":", ".join(unusedRaidMembers)},
                                 customIcon="warning")

    def resetInitializeDisk(self):
        self._initLabelAnswers = {}

    def questionInitializeDisk(self, path, description, size, name):
        retVal = False

        if not path:
            return retVal

        if path in self._initLabelAnswers:
            ctx.logger.info("Interface not asking about disk initialization, "
                            "using cached answer: %s" % self._initLabelAnswers[path])
            return self._initLabelAnswers[path]

        elif "all" in self._initLabelAnswers:
            ctx.logger.info("Interface not asking about disk initialization, "
                     "using cached answer: %s" % self._initLabelAnswers["all"])
            return self._initLabelAnswers["all"]

        rc = self.messageWindow(_("Error"),
                                _("Cannot access the partition table of %(description)s(%(name)s) -- %(size)-0.fMB\n\n"
                                  "If there already exists a partition table on this device, "
                                  "it will\n be re-initialized and your existing data will be lost!\n\n"
                                  "To re-initialize the current disk press Re-initialize.\n\n"
                                  "To re-initialize all disks with unaccessible partition tables press "
                                  "Re-initialize All")
                                  % {'name': name, 'size': size, 'description': description},
                                  type="custom",
                                  customButtons = [_("Ignore"), _("Ignore All"),
                                                   _("Re-initialize"), ("Re-initialize All") ],
                                  customIcon="question")
        if rc == 0:
            retVal = False
        elif rc == 1:
            path = "all"
            retVal = False
        elif rc == 2:
            retVal = True
        elif rc == 3:
            path = "all"
            retVal = True

        self._initLabelAnswers[path] = retVal
        return retVal

    def resetReinitInconsistentLVM(self):
        self._inconsistentLVMAnswers = {}

    def questionReinitInconsistentLVM(self, pv_names=None, lv_name=None, vg_name=None):

        retVal = False # The less destructive default
        allSet = frozenset(["all"])

        if not pv_names or (lv_name is None and vg_name is None):
            return retVal

        # We are caching answers so that we don't ask for ignoring
        # in each storage.reset() again (note that reinitialization is
        # done right after confirmation in dialog, not as a planned
        # action).
        key = frozenset(pv_names)
        if key in self._inconsistentLVMAnswers:
            ctx.logger.info("UI not asking about disk initialization, "
                            "using cached answer: %s" % self._inconsistentLVMAnswers[key])
            return self._inconsistentLVMAnswers[key]
        elif allSet in self._inconsistentLVMAnswers:
            ctx.logger.info("UI not asking about disk initialization, "
                            "using cached answer: %s" % self._inconsistentLVMAnswers[allSet])
            return self._inconsistentLVMAnswers[allSet]

        if vg_name is not None:
            message = "Volume Group %s" % vg_name
        elif lv_name is not None:
            message = "Logical Volume %s" % lv_name

        na = {'msg': message, 'pvs': ", ".join(pv_names)}
        rc = self.messageWindow(_("Warning"),
                                _("Error processing LVM.\n"
                                  "There is inconsistent LVM data on %(msg)s. You\ncan "
                                  "reinitialize all related PVs (%(pvs)s) which will\nerase "
                                  "the LVM metadata, or ignore which will preserve the\n"
                                  "contents.  This action may also be applied to all other "
                                  "PVs with\ninconsistent metadata.") % na, type="custom",
                                customButtons = [_("Ignore"), _("Ignore all"),
                                                 _("Re-initialize"), _("Re-initialize all") ],
                                customIcon="question")
        if rc == 0:
            retVal = False
        elif rc == 1:
            key = allSet
            retVal = False
        elif rc == 2:
            retVal = True
        elif rc == 3:
            key = allSet
            retVal = True

        self._inconsistentLVMAnswers[key] = retVal
        return retVal
