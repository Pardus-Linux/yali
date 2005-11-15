/*
* Copyright (c) 2005, TUBITAK/UEKAE
*
* This program is free software; you can redistribute it and/or modify it
* under the terms of the GNU General Public License as published by the
* Free Software Foundation; either version 2 of the License, or (at your
* option) any later version. Please read the COPYING file.
*/

#include <Python.h>
#include <unistd.h>
#include <sys/reboot.h>


PyDoc_STRVAR(fastreboot__doc__,
"fastreboot()\n"
"\n"
"sync() and reboot() if root user ;)!\n");

void
reboot_fastreboot(PyObject *self)
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

static PyMethodDef reboot_methods[] = {
    {"fastreboot",  (PyCFunction)reboot_fastreboot,  METH_NOARGS,  fastreboot__doc__},
    {NULL, NULL}
};

PyMODINIT_FUNC
initreboot(void)
{
    PyObject *m;

    m = Py_InitModule("reboot", reboot_methods);

    return;
}

