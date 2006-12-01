/*
* Copyright (c) 2005, TUBITAK/UEKAE
*
* This program is free software; you can redistribute it and/or modify it
* under the terms of the GNU General Public License as published by the
* Free Software Foundation; either version 2 of the License, or (at your
* option) any later version. Please read the COPYING file.
*/

#include <Python.h>
#include <sys/mount.h>
#include <sys/ioctl.h>
#include <linux/cdrom.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/reboot.h>


PyDoc_STRVAR(mount__doc__,
"mount(source, target, filesystem)\n"
"\n"
"method implements the mount(2) system call in Linux\n");

static PyObject*
yalisys_mount(PyObject *self, PyObject *args)
{

  int ok;
  const char *src, *tgt, *fstype;

  /* FIXME: get mount flags! */
  if (!PyArg_ParseTuple(args, "sss", &src, &tgt, &fstype))
  {
      Py_INCREF(Py_None);
      return Py_None;
  }

  ok = mount(src, tgt, fstype, MS_NOATIME, NULL);

  return PyInt_FromLong( (long) ok );
}



PyDoc_STRVAR(umount__doc__,
"umount(target)\n"
"\n"
"method implements the umount(2) system call in Linux\n");

static PyObject*
yalisys_umount(PyObject *self, PyObject *args)
{
  int ok;
  const char *tgt;

  if (!PyArg_ParseTuple(args, "s", &tgt))
  {
      Py_INCREF(Py_None);
      return Py_None;
  }

  ok = umount2(tgt, MNT_FORCE);

  return PyInt_FromLong( (long) ok );
}



PyDoc_STRVAR(eject__doc__,
"eject(mount_point)\n"
"ejects the cdrom mounted.\n"
"");

static PyObject*
yalisys_eject(PyObject *self, PyObject *args)
{
    int fd;
    const char *mount_point;

    if (!PyArg_ParseTuple(args, "s", &mount_point))
	goto failed;
    
    fd = open(mount_point, O_RDONLY|O_NONBLOCK, 0);
    if (fd == -1)
	goto failed;

    if (ioctl(fd, CDROMEJECT, 0))
	goto failed;


    close(fd);
    Py_INCREF(Py_True);
    return Py_True;

failed:
    if (fd != -1)
	close(fd);
    Py_INCREF(Py_False);
    return Py_False;
}



PyDoc_STRVAR(fastreboot__doc__,
"fastreboot()\n"
"\n"
"sync() and reboot() if root user ;)!\n");

void
yalisys_fastreboot(PyObject *self)
{

  if (getuid() != 0)
    {
      return;
    }

  sync();
  sync();
  sync();
  reboot(RB_AUTOBOOT);
}



static PyMethodDef yalisys_methods[] = {
    {"mount",  (PyCFunction)yalisys_mount,  METH_VARARGS,  mount__doc__},
    {"umount",  (PyCFunction)yalisys_umount,  METH_VARARGS,  umount__doc__},
    {"eject",  (PyCFunction)yalisys_eject,  METH_VARARGS,  eject__doc__},
    {"fastreboot",  (PyCFunction)yalisys_fastreboot,  METH_NOARGS,  fastreboot__doc__},
    {NULL, NULL}
};

PyMODINIT_FUNC
inityalisys(void)
{
    PyObject *m;

    m = Py_InitModule("yalisys", yalisys_methods);

    return;
}

