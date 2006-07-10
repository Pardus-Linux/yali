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
import mount
from string import ascii_letters
from string import digits

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
    tgt = os.path.join(consts.target_dir, "sys")
    os.system("mount --bind /sys %s" % tgt)



    pid = os.fork()
    if pid == 0: # in child
        os.chroot(consts.target_dir)
        os.system("/sbin/ldconfig")
        os.system("/sbin/update-environment")

        os.environ["PATH"]="/bin:/sbin:/usr/bin:/usr/sbin"
        os.execve("/bin/service", ["/bin/service", "comar", "start"], os.environ)

#         comar_out = open("/tmp/comar.out", "w")
#         comar_err = open("/tmp/comar.err", "w")
#         os.dup2(comar_out.fileno(), 1)
#         os.dup2(comar_err.fileno(), 2)

#         os.environ["PATH"]="/bin:/sbin:/usr/bin:/usr/sbin"
#         comar_path = "/usr/bin/comar"
#         os.execve(comar_path, ["/usr/bin/comar", "--debug", "perf"], os.environ)


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
    allowed_chars = ascii_letters + digits + '.' + '_' + '-'
    return len(text) == len(filter(lambda u: [x for x in allowed_chars if x == u], text))

def add_hostname(hostname = 'pardus'):
    hostname_file = os.path.join(consts.target_dir, 'etc/env.d/01hostname')
    hosts_file = os.path.join(consts.target_dir, 'etc/hosts')


    def getCont(x):
        return open(x).readlines()
    def getFp(x):
        return open(x, "w")

    hostname_fp, hosts_fp = getFp(hostname_file), getFp(hosts_file)
    hostname_contents = ""
    hosts_contents = ""
    if os.path.exists(hostname_file):
        hostname_contents = getCont(hostname_file)
    if os.path.exists(hosts_file):
        hosts_contents = getCont(hosts_file)

    if hostname_contents:
        for line in hostname_contents:
            if line.startswith('HOSTNAME'):
                line = 'HOSTNAME="%s"\n' % hostname
            hostname_fp.write(line)
        hostname_fp.close()
    else:
        hostname_fp.write('HOSTNAME="%s"\n' % hostname)

    if hosts_contents:
        for line in hosts_contents:
            if line.startswith('127.0.0.1'):
                line = '127.0.0.1\t\tlocalhost %s\n' % hostname
            hosts_fp.write(line)
        hosts_fp.close()
    else:
        hosts_fp.write('127.0.0.1\t\tlocalhost %s\n' % hostname)


def is_windows_boot(partition_path, file_system):
    m_dir = "/tmp/pcheck"
    if not os.path.isdir(m_dir):
        os.makedirs(m_dir)

    try:
        if file_system == "fat32":
            mount.mount(partition_path, m_dir, "vfat")
        else:
            mount.mount(partition_path, m_dir, file_system)
    except:
        return False

    exist = lambda f: os.path.exists(os.path.join(m_dir, f))

    if exist("boot.ini") or exist("command.com"):
        mount.umount(m_dir)
        return True
    else:
        mount.umount(m_dir)
        return False

