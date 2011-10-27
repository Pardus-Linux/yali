#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2010 TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#
import os
import sys
import gettext
_ = gettext.translation('yali', fallback=True).ugettext

import yali
import yali.context as ctx


def load_kernel_modules():
    """
        Load kernel modules for LVM and RAID.

        Modules:

        -bqa    : --use-blacklist, --quiet, --all (insert all modules given as arguments)
        dm-mod  : LVM2 module
        raid0   : RAID0 module
        raid1   : RAID1 module
        raid456 : RAID 4, 5, 6 module
        raid10  : A raid module that combines features of both raid0 (striping) and raid1 (mirroring or plexing) - http://neil.brown.name/blog/20040827225440
    """

    # TODO: Check if the modules are loaded correctly
    os.system("modprobe -bqa dm-mod raid0 raid1 raid456 raid10")


def setup_environment():
    """
        Setup environment.
        Supress "LVM file descriptor left open" warning.
    """
    import locale
    #FIXME: Why do we need this?
    locale.setlocale(locale.LC_ALL, "")
    os.environ['LC_NUMERIC'] = 'C'
    os.environ["LVM_SUPPRESS_FD_WARNINGS"] = "1"


def setup_exception_handler():
    """
        Overrides Python's exception handler to show pretty exceptions.
    """
    import signal
    import traceback
    import cStringIO

    def signal_handler(sig, frame):
        if sig == signal.SIGTERM:
            sys.exit(1)

    def exception_handler(exception, value, error_traceback):
        signal.signal(signal.SIGINT, signal.SIG_IGN)   # Disable further interrupts

        sio = cStringIO.StringIO()

        sio.write(_("Please file a bug report to <http://bugs.pardus.org.tr>.\n"))

        _value = ''
        for arg in value.args:
            _value += str(arg) + '\n'

        sio.write(_value)
        sio.write(str(exception))
        sio.write('\n\n')
        sio.write(_("Backtrace:"))
        sio.write('\n')
        traceback.print_tb(error_traceback, None, sio)

        sio.seek(0)
        exception_traceback =  unicode(sio.read())

        ctx.logger.debug(_("Unhandled internal YALI exception:%s") % exception_traceback)

        if ctx.interface:
            ctx.interface.exceptionWindow(exception, exception_traceback)

    sys.excepthook = exception_handler
    signal.signal(signal.SIGTERM, signal_handler)


def init_gui_interface():
    """
        Initializes YALI specific GUI elements such as message boxes and draggable widgets.
    """
    from yali.gui.interface import Interface
    ctx.interface = Interface()


def init_gui_runner():
    """
        Load the graphical user interface.
    """
    from yali.gui.runner import Runner
    gui_runner = Runner()
    gui_runner.run()


def load_options(argv=None):
    from optparse import OptionParser
    parser = OptionParser()

    parser.add_option("-d",
                      "--debug",
                      dest="debug",
                      action="store_true",
                      default=False,
                      help="enable debug")

    parser.add_option("-c",
                      "--config",
                      dest="conffile",
                      help="Use alternate configuration file",
                      metavar="FILE")

    parser.add_option("--dryRun",
                      dest="dryRun",
                      action="store_true",
                      help="only show the result")

    parser.add_option("--baseonly",
                      dest="baseonly",
                      action="store_true",
                      help="install base system packages")

    parser.add_option("--enable-collection",
                      dest="collection",
                      action="store_true",
                      default=False,
                      help="install collection base installation"
                           " if collections exist")

    parser.add_option("--system",
                      dest="install_type",
                      default=0,
                      action="store_const",
                      const= 1,
                      help="start system installation")

    parser.add_option("--firstboot",
                      dest="install_type",
                      action="store_const",
                      const=2,
                      help="start with first boot options")

    parser.add_option("--rescue",
                      dest="install_type",
                      action="store_const",
                      const=3,
                      help="start Yali with rescue mode")

    parser.add_option("--oem",
                      dest="install_type",
                      action="store_const",
                      const=4,
                      help="start Yali with oem mode")

    # TODO: Implement YALI Autopilot
    """
    parser.add_option("--kahya",
                      dest="kahya",
                      help="run with Kahya file",
                      metavar="FILE")
    """

    parser.add_option("-s",
                      "--startFrom",
                      dest="startFrom",
                      type="int",
                      default=0,
                      help="start from the given screen (num)")

    parser.add_option("-t",
                      "--theme",
                      dest="theme",
                      help="load given theme",
                      type="str",
                      default="pardus")

    parser.add_option("-b",
                      "--branding",
                      dest="branding",
                      help="load given branding",
                      type="str",
                      default="pardus")

    return parser.parse_args(argv)


def load_config(options):
    """
        Reads YALI configuration file and sets installation options.

        Arguments:
            parser: Options parsed with ConfigParser module
            options: Options parsed with optparse module
    """

    # Check if yali.conf exists
    if not os.path.exists(ctx.consts.conf_file):
        ctx.logger.debug(_("%s is missing") % ctx.consts.conf_file)
        sys.exit(1)

    import ConfigParser
    parser = ConfigParser.ConfigParser()

    try:
        parser.read(ctx.consts.conf_file)
    except IOError:
        ctx.logger.debug(_("%s is corrupted") % ctx.consts.conf_file)
        sys.exit(1)

    if parser.has_option("general", "installation"):
        install_types = {"system"    : ctx.STEP_BASE,
                         "firstboot" : ctx.STEP_FIRST_BOOT,
                         "rescue"    : ctx.STEP_RESCUE,
                         "oem"       : ctx.STEP_OEM_INSTALL,
                         "default"   : ctx.STEP_DEFAULT}

        options.install_type = install_types[parser.get("general", "installation")]

    if parser.has_option("general", "debug"):
        options.debug = parser.getboolean("general", "debug")

    if parser.has_option("general", "collection"):
        options.collection = parser.getboolean("general", "collection")

    if parser.has_option("general", "baseonly"):
        options.baseonly = parser.getboolean("general", "baseonly")

    if parser.has_option("general", "dryrun"):
        options.dryRun = parser.getboolean("general", "dryrun")

    if parser.has_option("general", "theme"):
        options.theme = parser.get("general", "theme")

    if parser.has_option("general", "branding"):
        options.theme = parser.get("general", "branding")


def check_plymouth():
    """
        Closes plymouth splash if necessary.
    """
    try:
        if os.path.exists("/bin/plymouth") and not os.system("/bin/plymouth --ping"):
            os.system("/bin/plymouth quit --retain-splash")
    except:
        ctx.logger.debug("ERROR: There is a problem with plymouth")


def root_access(function):
    """
        Checks if the user has root access.
    """
    if os.getuid() != 0:
        print "%s must be run as root." % sys.argv[0]
        sys.exit(1)

    return function


@root_access
def main():
    """
        YALI main function.
    """

    # Terminate plymouth daemon if needed
    check_plymouth()

    # Log the starting action
    ctx.logger.debug("YALI Started")

    # Load kernel modules needed for LVM and RAID access
    load_kernel_modules()

    # Set locale and supress LVM warnings
    setup_environment()

    # Initialize YALI specific GUI elements
    init_gui_interface()

    # Override Python's exception handler to show pretty exceptions
    setup_exception_handler()

    # Set command line arguments as YALI Options
    (options, args) = load_options()

    # Set configuration file arguments as YALI Options
    # !!! Overrides command line arguments !!!
    load_config(options)

    ctx.flags.install_type = options.install_type
    ctx.flags.startup      = options.startFrom
    ctx.flags.debug        = options.debug
    ctx.flags.dryRun       = options.dryRun
    ctx.flags.collection   = options.collection
    ctx.flags.baseonly     = options.baseonly
    ctx.flags.theme        = options.theme
    ctx.flags.branding     = options.branding

    # TODO: Implement YALI Autopilot
    """
    if options.kahya:
        ctx.flags.kahya = True
        ctx.flags.kahyaFile = options.kahya
    """

    if not ctx.storage:
        from yali.storage import Storage
        ctx.storage = Storage()

    if not ctx.bootloader:
        from yali.storage.bootloader import BootLoader
        ctx.bootloader = BootLoader(ctx.storage)

    # Set kernel parameters as YALI Options
    # !!! Overrides configuration file !!!
    #ctx.flags.parse_kernel_options(ctx)

    # Show the user interface
    init_gui_runner()


if __name__ == "__main__":
    sys.exit(main())
