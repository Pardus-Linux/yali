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

# sysutils module provides basic system utilities

import os
from string import ascii_letters

from yali.constants import consts

def find_executable(exec_name):
    # preppend /bin, /sbin explicitly to handle system configuration
    # errors
    paths = ["/bin", "/sbin"]

    paths.extend(os.getenv("PATH").split(':'))

    for p in paths:
        exec_path = os.path.join(p, exec_name)
        if os.path.exists(exec_path):
            return exec_path

    return None

    
##
# run comar daemon in chroot
def chroot_comar():

    # FIXME: use mount module (needs options support)
    tgt = os.path.join(consts.target_dir, "dev")
    os.system("mount --bind /dev %s" % tgt)
    tgt = os.path.join(consts.target_dir, "proc")
    os.system("mount --bind /proc %s" % tgt)

    pid = os.fork()
    if pid == 0: # in child
        os.chroot(consts.target_dir)
        os.system("/sbin/ldconfig")

        comar_out = open("/tmp/comar.out", "w")
        comar_err = open("/tmp/comar.err", "w")
        os.dup2(comar_out.fileno(), 1)
        os.dup2(comar_err.fileno(), 2)

        os.environ["PATH"]="/bin:/sbin:/usr/bin:/usr/sbin"
        comar_path = "/usr/bin/comar"
        os.execve(comar_path, ["/usr/bin/comar", "--debug", "perf"], os.environ)


def swap_as_file(filepath, mb_size):
    dd, mkswap = find_executable('dd'), find_executable('mkswap')
   
    if (not dd) or (not mkswap): return False
   
    create_swap_file = "%s if=/dev/zero of=%s bs=1024 count=%d" % (dd, filepath, (int(mb_size)*1024))
    mk_swap          = "%s %s" % (mkswap, filepath)

    try:
        for cmd in [create_swap_file, mk_swap]:
            p = os.popen(cmd)
            p.close()
        os.chmod(filepath, 0600)
    except:
        return False

    return True


##
# total memory size
def mem_total():
    m = open("/proc/meminfo")
    for l in m:
        if l.startswith("MemTotal"):
            return int(l.split()[1]) / 1024
            
    return None



def text_is_valid(text):
    allowed_chars = ascii_letters + '.' + '_' + '-'
    return len(text) == len(filter(lambda u: [x for x in allowed_chars if x == u], text))

def add_hostname(hostname = 'pardus'):
    hostname_file = os.path.join(consts.target_dir, 'etc/conf.d/hostname')
    hosts_file = os.path.join(consts.target_dir, 'etc/hosts')

    getCont, getFp = lambda x: open(x).readlines(), lambda x: open(x, 'w')

    hostname_contents, hosts_contents = getCont(hostname_file), getCont(hosts_file)
    hostname_fp, hosts_fp = getFp(hostname_file), getFp(hosts_file)

    for line in hostname_contents:
        if line.startswith('HOSTNAME'):
            line = 'HOSTNAME="%s"\n' % hostname
        hostname_fp.write(line)
    hostname_fp.close()

    for line in hosts_contents:
        if line.startswith('127.0.0.1'):
            line = '127.0.0.1\t\tlocalhost %s\n' % hostname
        hosts_fp.write(line)
    hosts_fp.close()

