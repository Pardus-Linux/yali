#!/usr/bin/python
# -*- coding: utf-8 -*-

import gettext

__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

import yali.context as ctx
from yali.gui.YaliDialog import MessageWindow


class Interface(object):
    def __init__(self):
        self._initLabelAnswers = {}
        self._inconsistentLVMAnswers = {}

    def informationWindow(self):
        pass

    def messageWindow(self, title, text, type="ok", default=None, customButtons=None, customIcon=None):
        return MessageWindow(title, text, type, default, customButtons, customIcon, run=True).rc

    def detailedMessageWindow(self, title, text, longText, type="ok", default=None, customButtons=None, customIcon=None):
        return MessageWindow(title, text, type, default, customButtons, customIcon, run=True, detailed=True, longText=longText).rc

    def resetInitializeDisk(self):
        self._initLabelAnswers = {}

    def questionInitializeDisk(path, description, size, details):
        rc = self.messageWindow(_("Warning"),
                                _("Error processing drive:\n\n"
                                  "%(path)s\n%(size)-0.fMB\n%(description)s\n\n"
                                  "This device may need to be reinitialized.\n\n"
                                  "REINITIALIZING WILL CAUSE ALL DATA TO BE LOST!\n\n"
                                  "This operation may also be applied to all other disks "
                                  "needing reinitialization.%(details)s")
                                  % {'path': path, 'size': size,
                                     'description': description, 'details': details},
                                  type="custom",
                                  customButtons = [_("Ignore"), _("Ignore all"),
                                                   _("Re-initialize"), ("Re-initialize all") ],
                                  customIcon="question")
        if rc == 0:
            return False
        elif rc == 1:
            return False
        elif rc == 2:
            return True
        elif rc == 3:
            return True
        else:
            return True

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
                                  "There is inconsistent LVM data on %(msg)s.  You can "
                                  "reinitialize all related PVs (%(pvs)s) which will erase "
                                  "the LVM metadata, or ignore which will preserve the "
                                  "contents.  This action may also be applied to all other "
                                  "PVs with inconsistent metadata.") % na, type="custom",
                                customButtons = [_("Ignore"), _("Ignore _all"),
                                                 _("Re-initialize"), _("Re-ini_tialize all") ],
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
