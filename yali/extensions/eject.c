/*
* Copyright (c) 2005, TUBITAK/UEKAE
*
* This program is free software; you can redistribute it and/or modify it
* under the terms of the GNU General Public License as published by the
* Free Software Foundation; either version 2 of the License, or (at your
* option) any later version. Please read the COPYING file.
*/

#include <Python.h>
#include <sys/ioctl.h>
#include <linux/cdrom.h>


PyDoc_STRVAR(eject__doc__,
"eject(file_descriptor)\n"
"ejects the cdrom mounted with the given file descriptor.\n"
"Usage:\n"
"eject.eject(os.open('/path/', os.O_RDONLY|os.O_NONBLOCK))"
"");

static PyObject *
eject_eject(PyObject *self, PyObject *args)
{
    int d;

    if (!PyArg_ParseTuple(args, "i", &d)) return NULL;
    if (ioctl(d, CDROMEJECT, 1)) {
	Py_INCREF(Py_False);
	return Py_False;
    }

    Py_INCREF(Py_True);
    return Py_True;
}

static PyMethodDef eject_methods[] = {
    {"eject",  (PyCFunction)eject_eject,  METH_VARARGS,  eject__doc__},
    {NULL, NULL}
};

PyMODINIT_FUNC
initeject(void)
{
    PyObject *m;

    m = Py_InitModule("eject", eject_methods);

    return;
}

