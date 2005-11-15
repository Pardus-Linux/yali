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


PyDoc_STRVAR(mount__doc__,
"mount(source, target, filesystem)\n"
"\n"
"method implements the mount(2) system call in Linux\n");

PyObject*
mount_mount(PyObject *self, PyObject *args)
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

PyObject*
mount_umount(PyObject *self, PyObject *args)
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

static PyMethodDef mount_methods[] = {
    {"mount",  (PyCFunction)mount_mount,  METH_VARARGS,  mount__doc__},
    {"umount",  (PyCFunction)mount_umount,  METH_VARARGS,  umount__doc__},
    {NULL, NULL}
};

PyMODINIT_FUNC
initmount(void)
{
    PyObject *m;

    m = Py_InitModule("mount", mount_methods);

    return;
}

