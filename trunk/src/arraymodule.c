/**
 *  $File: arraymodule.c $
 *  $LastChangedDate$
 *  $Rev$
 *
 *  This file is part of simuPOP, a forward-time population genetics
 *  simulation environment. Please visit http://simupop.sourceforge.net
 *  for details.
 *
 *  Copyright (C) 2004 - 2009 Bo Peng (bpeng@mdanderson.org)
 *
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program. If not, see <http://www.gnu.org/licenses/>.
 */


/* this is modified from arraymodule.c from the standard python distribution. */

#include "Python.h"
#include "structmember.h"

#ifdef STDC_HEADERS
#include <stddef.h>
#else                                                                                         /* !STDC_HEADERS */
#ifndef DONT_HAVE_SYS_TYPES_H
#include <sys/types.h>                                                        /* For size_t */
#endif                                                                                        /* DONT_HAVE_SYS_TYPES_H */
#endif                                                                                        /* !STDC_HEADERS */

/// CPPONLY
struct arrayobject;                                                             /* Forward */

/** All possible arraydescr values are defined in the vector "descriptors"
 * below.    That's defined later because the appropriate get and set
 * functions aren't visible yet.
 CPPONLY
 */
struct arraydescr
{
    int typecode;
    int itemsize;
    PyObject * (*getitem)(struct arrayobject *, int);
    int (*setitem)(struct arrayobject *, int, PyObject *);
};

/// CPPONLY
typedef struct arrayobject
{
    PyObject_VAR_HEAD
    // pointer to the beginning of the item.
    struct iterator
    {
        char *ob_item;
        // this will be used by binary type only.
        GenoIterator ob_iter;
    } ob_iterator;
    // description of the type, the exact get and set item functions.
    struct arraydescr *ob_descr;
} arrayobject;

// redefinition of type...
// staticforward PyTypeObject Arraytype;

/// CPPONLY
bool is_carrayobject(PyObject *op);

// #define is_carrayobject(op) ((op)->ob_type == &Arraytype)

/****************************************************************************
Get and Set functions for each type.
A Get function takes an arrayobject* and an integer index, returning the
array value at that index wrapped in an appropriate PyObject*.
A Set function takes an arrayobject, integer index, and PyObject*; sets
the array value at that index to the raw C data extracted from the PyObject*,
and returns 0 if successful, else nonzero on failure (PyObject* not of an
appropriate type or value).
Note that the basic Get and Set functions do NOT check that the index is
in bounds; that's the responsibility of the caller.
****************************************************************************/

// allele type
/// CPPONLY
static PyObject *
a_getitem(arrayobject *ap, int i)
{
    return PyInt_FromLong( *(ap->ob_iterator.ob_iter+i) );
}


/// CPPONLY
static int
a_setitem(arrayobject *ap, int i, PyObject *v)
{
	// right now, the longest allele is uint16_t, but we need to be careful.
    int x;
    /* PyArg_Parse's 'b' formatter is for an unsigned char, therefore
         must use the next size up that is signed ('h') and manually do
         the overflow checking */
    if (!PyArg_Parse(v, "i;array item must be integer", &x))
        return -1;
    // force the value to bool to avoid a warning
#ifdef BINARYALLELE
    *(ap->ob_iterator.ob_iter+i) = (x != 0);
#else
    *(ap->ob_iterator.ob_iter+i) = Allele(x);
#endif
    return 0;
}


/// CPPONLY
static PyObject *
f_getitem(arrayobject *ap, int i)
{
    return PyFloat_FromDouble((double) ((float *)ap->ob_iterator.ob_item)[i]);
}


/// CPPONLY
static int
f_setitem(arrayobject *ap, int i, PyObject *v)
{
    float x;
    if (!PyArg_Parse(v, "f;array item must be float", &x))
        return -1;
    if (i >= 0)
        ((float *)ap->ob_iterator.ob_item)[i] = x;
    return 0;
}


/// CPPONLY
static PyObject *
d_getitem(arrayobject *ap, int i)
{
    return PyFloat_FromDouble(((double *)ap->ob_iterator.ob_item)[i]);
}


/// CPPONLY
static int
d_setitem(arrayobject *ap, int i, PyObject *v)
{
    double x;
    if (!PyArg_Parse(v, "d;array item must be float", &x))
        return -1;
    if (i >= 0)
        ((double *)ap->ob_iterator.ob_item)[i] = x;
    return 0;
}

/// CPPONLY
static PyObject *
i_getitem(arrayobject *ap, int i)
{
    return PyInt_FromLong((long) ((int *)ap->ob_iterator.ob_item)[i]);
}


/// CPPONLY
static int
i_setitem(arrayobject *ap, int i, PyObject *v)
{
    int x;
    /* 'i' == signed int, maps to PyArg_Parse's 'i' formatter */
    if (!PyArg_Parse(v, "i;array item must be integer", &x))
        return -1;
    if (i >= 0)
        ((int *)ap->ob_iterator.ob_item)[i] = x;
    return 0;
}


/* Description of types */
static struct arraydescr descriptors[] =
{
    {'a', 0, a_getitem, a_setitem},
    {'f', sizeof(float), f_getitem, f_setitem},
    {'d', sizeof(double), d_getitem, d_setitem},
    {'i', sizeof(int), i_getitem, i_setitem},
    {                                                                                             /* Sentinel */
        '\0', 0, 0, 0
    }
};

/****************************************************************************
Implementations of array object methods.
****************************************************************************/
// you can not create a object from python,
// error will occur
/// CPPONLY
static PyObject *
carray_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    PyErr_SetString(PyExc_TypeError,
        "Can not create carray object from python.");
    return NULL;
}


// you can not init a object from python,
// error will occur
/// CPPONLY
static PyObject *
carray_init(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    PyErr_SetString(PyExc_TypeError,
        "Can not create carray object from python.");
    return NULL;
}


// declaration only to avoid use of Arraytype
/// CPPONLY
PyObject * newcarrayobject(char* ptr, char type, int size);
/// CPPONLY
PyObject * newcarrayiterobject(GenoIterator begin, GenoIterator end);

/// CPPONLY
static PyObject * getarrayitem(PyObject *op, int i)
{
    register arrayobject *ap;
    assert(is_carrayobject(op));
    ap = (arrayobject *)op;
    if (i < 0 || i >= ap->ob_size)
    {
        // use automatic increase of size?
        PyErr_SetString(PyExc_IndexError, "array index out of range");
        return NULL;
    }
    return (*ap->ob_descr->getitem)(ap, i);
}


/// CPPONLY
static void
array_dealloc(arrayobject *op)
{
    PyObject_Del(op);
}


/// CPPONLY
static PyObject *
array_richcompare(PyObject *v, PyObject *w, int op)
{
    // will really has this case?
    if (!is_carrayobject(v) && !is_carrayobject(w))
    {
        Py_INCREF(Py_NotImplemented);
        return Py_NotImplemented;
    }

    // both are array
    if( is_carrayobject(v) && is_carrayobject(w) )
    {
        arrayobject *va, *wa;
        PyObject *vi = NULL;
        PyObject *wi = NULL;
        int i, k;
        PyObject *res;

        va = (arrayobject *)v;
        wa = (arrayobject *)w;

        if (va->ob_size != wa->ob_size && (op == Py_EQ || op == Py_NE))
        {
            /* Shortcut: if the lengths differ, the arrays differ */
            if (op == Py_EQ)
                res = Py_False;
            else
                res = Py_True;
            Py_INCREF(res);
            return res;
        }

        /* Search for the first index where items are different */
        k = 1;
        for (i = 0; i < va->ob_size && i < wa->ob_size; i++)
        {
            vi = getarrayitem(v, i);
            wi = getarrayitem(w, i);
            if (vi == NULL || wi == NULL)
            {
                Py_XDECREF(vi);
                Py_XDECREF(wi);
                return NULL;
            }
            k = PyObject_RichCompareBool(vi, wi, Py_EQ);
            if (k == 0)
                break;                                                                        /* Keeping vi and wi alive! */
            Py_DECREF(vi);
            Py_DECREF(wi);
            if (k < 0)
                return NULL;
        }

        if (k)
        {
            /* No more items to compare -- compare sizes */
            int vs = va->ob_size;
            int ws = wa->ob_size;
            int cmp;
            switch (op)
            {
                case Py_LT: cmp = vs <    ws; break;
                case Py_LE: cmp = vs <= ws; break;
                case Py_EQ: cmp = vs == ws; break;
                case Py_NE: cmp = vs != ws; break;
                case Py_GT: cmp = vs >    ws; break;
                case Py_GE: cmp = vs >= ws; break;
                default: return NULL;                                         /* cannot happen */
            }
            if (cmp)
                res = Py_True;
            else
                res = Py_False;
            Py_INCREF(res);
            return res;
        }
        /* We have an item that differs.    First, shortcuts for EQ/NE */
        if (op == Py_EQ)
        {
            Py_INCREF(Py_False);
            res = Py_False;
        }
        else if (op == Py_NE)
        {
            Py_INCREF(Py_True);
            res = Py_True;
        }
        else
        {
            /* Compare the final item again using the proper operator */
            res = PyObject_RichCompare(vi, wi, op);
        }
        Py_DECREF(vi);
        Py_DECREF(wi);
        return res;
    }
    else
    {
        arrayobject *va;
        PyObject* wa, *res;
        bool dir;
        int vs, ws;                                                                     // direction

        // one of them is not array
        if( is_carrayobject(v) )
        {
            va = (arrayobject *)v;
            wa = w;
            dir = true;
        }
        else
        {
            va = (arrayobject *)w;
            wa = v;
            dir = false;
        }

        if( ! PySequence_Check(wa) )
        {
            // use automatic increase of size?
            PyErr_SetString(PyExc_IndexError, "only sequence can be compared");
            return NULL;
        }

        vs = va->ob_size;
        ws = PySequence_Size(wa);

        if (vs != ws && (op == Py_EQ || op == Py_NE))
        {
            /* Shortcut: if the lengths differ, the arrays differ */
            if (op == Py_EQ)
                res = Py_False;
            else
                res = Py_True;
            Py_INCREF(res);
            return res;
        }

        /* Search for the first index where items are different */
        PyObject * vi = NULL;
	PyObject * wi = NULL;
        int k = 1;
        for (int i = 0; i < vs && i < ws; i++)
        {
            vi = getarrayitem((PyObject*)(va), i);
            wi = PySequence_GetItem(wa, i);
            if (vi == NULL || wi == NULL)
            {
                Py_XDECREF(vi);
                Py_XDECREF(wi);
                return NULL;
            }
            k = PyObject_RichCompareBool(vi, wi, Py_EQ);
            if (k == 0)
                break;                                                                        /* Keeping vi and wi alive! */
            Py_DECREF(vi);
            Py_DECREF(wi);
            // -1 for error
            if (k < 0)
                return NULL;
        }

        if (k)                                                                                // if equal
        {
            /* No more items to compare -- compare sizes */
            int cmp;
            switch (op)
            {
                case Py_LT: cmp = vs <    ws; break;
                case Py_LE: cmp = vs <= ws; break;
                case Py_EQ: cmp = vs == ws; break;
                case Py_NE: cmp = vs != ws; break;
                case Py_GT: cmp = vs >    ws; break;
                case Py_GE: cmp = vs >= ws; break;
                default: return NULL;                                         /* cannot happen */
            }
            if ((cmp && dir) || (!cmp && !dir))
                res = Py_True;
            else
                res = Py_False;
            Py_INCREF(res);
            return res;
        }

        /* We have an item that differs.    First, shortcuts for EQ/NE */
        if (op == Py_EQ)
        {
            Py_INCREF(Py_False);
            res = Py_False;
        }
        else if (op == Py_NE)
        {
            Py_INCREF(Py_True);
            res = Py_True;
        }
        else
        {
            /* Compare the final item again using the proper operator */
            int r = PyObject_RichCompareBool(vi, wi, op);
            if( (r==0 && dir) || (r!=0 && !dir) )             // false
            {
                Py_INCREF(Py_False);
                res = Py_False;
            }
            else
            {
                Py_INCREF(Py_True);
                res = Py_True;
            }
        }
        Py_DECREF(vi);
        Py_DECREF(wi);
        return res;
    }
}


/// CPPONLY
static Py_ssize_t array_length(arrayobject *a)
{
    return a->ob_size;
}


/// CPPONLY
static PyObject * array_concat(arrayobject *a, PyObject *bb)
{
    PyErr_SetString(PyExc_TypeError,
        "Can not concat carray object.");
    return NULL;
}


/// CPPONLY
static PyObject * array_repeat(arrayobject *a, Py_ssize_t n)
{
    PyErr_SetString(PyExc_TypeError,
        "Can not repeat carray object.");
    return NULL;
}


/// CPPONLY
static PyObject * array_item(arrayobject *a, Py_ssize_t i)
{
    if (i < 0 || i >= a->ob_size)
    {
        PyErr_SetString(PyExc_IndexError, "array index out of range");
        return NULL;
    }
    return getarrayitem((PyObject *)a, i);
}


/// CPPONLY
static PyObject * array_slice(arrayobject *a, Py_ssize_t ilow, Py_ssize_t ihigh)
{
    arrayobject *np;
    if (ilow < 0)
        ilow = 0;
    else if (ilow > a->ob_size)
        ilow = a->ob_size;
    if (ihigh < 0)
        ihigh = 0;
    if (ihigh < ilow)
        ihigh = ilow;
    else if (ihigh > a->ob_size)
        ihigh = a->ob_size;
    if( a->ob_descr->typecode == 'a')
        np = (arrayobject *) newcarrayiterobject(a->ob_iterator.ob_iter + ilow,
            a->ob_iterator.ob_iter + ihigh);
    else
        np = (arrayobject *) newcarrayobject(a->ob_iterator.ob_item + ilow*a->ob_descr->itemsize,
            a->ob_descr->typecode, ihigh - ilow);
    if (np == NULL)
        return NULL;
    return (PyObject *)np;
}


/// CPPONLY
static int array_ass_slice(arrayobject *a, Py_ssize_t ilow, Py_ssize_t ihigh, PyObject *v)
{
    if (v == NULL || a==(arrayobject*)v)
    {
        PyErr_BadArgument();
        return -1;
    }

    if (ilow < 0)
        ilow = 0;
    else if (ilow > a->ob_size)
        ilow = a->ob_size;
    if (ihigh < 0)
        ihigh = 0;
    if (ihigh < ilow)
        ihigh = ilow;
    else if (ihigh > a->ob_size)
        ihigh = a->ob_size;

    // use a single number to propagate v
    if( PyNumber_Check(v) )
    {
        for(int i=ilow; i<ihigh; ++i)
            (*a->ob_descr->setitem)(a, i, v);
        return 0;
    }
#define b ((arrayobject *)v)
    if(is_carrayobject(v))                                                    /* v is of array type */
    {
        int n = b->ob_size;
        if (b->ob_descr != a->ob_descr)
        {
            PyErr_BadArgument();
            return -1;
        }
        if( n != ihigh - ilow)
        {
            PyErr_SetString(PyExc_ValueError, "Can not extend or thrink slice");
            return -1;
        }
        if( a->ob_descr->typecode != 'a')
            memcpy(a->ob_iterator.ob_item + ilow * a->ob_descr->itemsize,
                b->ob_iterator.ob_item, (ihigh-ilow) * a->ob_descr->itemsize);
        else
        {
            for(int i=0; i<n; ++i)
                (*a->ob_descr->setitem)(a, i+ilow, (*b->ob_descr->getitem)(b,i) );
        }
        return 0;
    }
#undef b
    /* a general sequence */
    if( PySequence_Check(v) )
    {
        int n = PySequence_Size(v);
        if( n != ihigh - ilow)
        {
            PyErr_SetString(PyExc_ValueError, "Can not extend or thrink slice");
            return -1;
        }
        // iterator sequence
        for(int i=0; i<n; ++i)
        {
            PyObject* item = PySequence_GetItem(v, i);
            (*a->ob_descr->setitem)(a, i+ilow, item);
            Py_DECREF(item);
        }
        return 0;
    }
    PyErr_SetString(PyExc_ValueError, "Only number or list can be assigned");
    return -1;
}


/// CPPONLY
static Py_ssize_t array_ass_item(arrayobject *a, Py_ssize_t i, PyObject *v)
{
    if (i < 0 || i >= a->ob_size)
    {
        PyErr_SetString(PyExc_IndexError,
            "array assignment index out of range");
        return -1;
    }
    if (v == NULL)
        return array_ass_slice(a, i, i+1, v);
    return (*a->ob_descr->setitem)(a, i, v);
}


/* not used */
/*
static int setarrayitem(PyObject *a, int i, PyObject *v)
{
    assert(is_carrayobject(a));
    return array_ass_item((arrayobject *)a, i, v);
}
*/

/// CPPONLY
static PyObject * array_count(arrayobject *self, PyObject *args)
{
    int count = 0;
    int i;
    PyObject *v;

    if (!PyArg_ParseTuple(args, "O:count", &v))
        return NULL;
    for (i = 0; i < self->ob_size; i++)
    {
        PyObject *selfi = getarrayitem((PyObject *)self, i);
        int cmp = PyObject_RichCompareBool(selfi, v, Py_EQ);
        Py_DECREF(selfi);
        if (cmp > 0)
            count++;
        else if (cmp < 0)
            return NULL;
    }
    return PyInt_FromLong((long)count);
}


/// CPPONLY
static char count_doc [] =
"count(x)\n\
\n\
Return number of occurences of x in the array.";

/// CPPONLY
static PyObject * array_index(arrayobject *self, PyObject *args)
{
    int i;
    PyObject *v;

    if (!PyArg_ParseTuple(args, "O:index", &v))
        return NULL;
    for (i = 0; i < self->ob_size; i++)
    {
        PyObject *selfi = getarrayitem((PyObject *)self, i);
        int cmp = PyObject_RichCompareBool(selfi, v, Py_EQ);
        Py_DECREF(selfi);
        if (cmp > 0)
        {
            return PyInt_FromLong((long)i);
        }
        else if (cmp < 0)
            return NULL;
    }
    PyErr_SetString(PyExc_ValueError, "array.index(x): x not in list");
    return NULL;
}


static char index_doc [] =
"index(x)\n\
\n\
Return index of first occurence of x in the array.";

/// CPPONLY
static PyObject * array_tolist(arrayobject *self, PyObject *args)
{
    PyObject *list = PyList_New(self->ob_size);
    int i;
    if (!PyArg_ParseTuple(args, ":tolist"))
        return NULL;
    if (list == NULL)
        return NULL;
    for (i = 0; i < self->ob_size; i++)
    {
        PyObject *v = getarrayitem((PyObject *)self, i);
        if (v == NULL)
        {
            Py_DECREF(list);
            return NULL;
        }
        PyList_SetItem(list, i, v);
    }
    return list;
}


static char tolist_doc [] =
"tolist() -> list\n\
\n\
Convert array to an ordinary list with the same items.";

PyMethodDef array_methods[] =
{
    {
        "count", (PyCFunction)array_count, METH_VARARGS,
        count_doc
    },
    {
        "index", (PyCFunction)array_index, METH_VARARGS,
        index_doc
    },
    {
        "tolist",    (PyCFunction)array_tolist,    METH_VARARGS,
        tolist_doc
    },
    {                                                                                             /* sentinel */
        NULL,        NULL
    }
};

/// CPPONLY
static PyObject * array_getattr(arrayobject *a, char *name)
{
    if (strcmp(name, "typecode") == 0)
    {
        char tc = a->ob_descr->typecode;
        return PyString_FromStringAndSize(&tc, 1);
    }
    if (strcmp(name, "itemsize") == 0)
    {
        return PyInt_FromLong((long)a->ob_descr->itemsize);
    }
    if (strcmp(name, "__members__") == 0)
    {
        PyObject *list = PyList_New(2);
        if (list)
        {
            PyList_SetItem(list, 0,
                PyString_FromString("typecode"));
            PyList_SetItem(list, 1,
                PyString_FromString("itemsize"));
            if (PyErr_Occurred())
            {
                Py_DECREF(list);
                list = NULL;
            }
        }
        return list;
    }
    return Py_FindMethod(array_methods, (PyObject *)a, name);
}


/// CPPONLY
static int array_print(arrayobject *a, FILE *fp, int flags)
{
    int ok = 0;
    int i, len;
    PyObject *v;
    len = a->ob_size;
    if (len == 0)
    {
        fprintf(fp, "[]");
        return ok;
    }
    fprintf(fp, "[");
    for (i = 0; i < len && ok == 0; i++)
    {
        if (i > 0)
            fprintf(fp, ", ");
        v = (a->ob_descr->getitem)(a, i);
        ok = PyObject_Print(v, fp, 0);
        Py_XDECREF(v);
    }
    fprintf(fp, "]");
    return ok;
}


/// CPPONLY
static PyObject *
array_repr(arrayobject *a)
{
    char buf[256];
    PyObject *s, *t, *comma, *v;
    int i, len;
    len = a->ob_size;
    if (len == 0)
    {
        PyOS_snprintf(buf, sizeof(buf), "[]");
        return PyString_FromString(buf);
    }
    PyOS_snprintf(buf, sizeof(buf), "[");
    s = PyString_FromString(buf);
    comma = PyString_FromString(", ");
    for (i = 0; i < len && !PyErr_Occurred(); i++)
    {
        if (i > 0)
            PyString_Concat(&s, comma);
        v = (a->ob_descr->getitem)(a, i);
        t = PyObject_Repr(v);
        Py_XDECREF(v);
        PyString_ConcatAndDel(&s, t);
    }
    Py_XDECREF(comma);
    PyString_ConcatAndDel(&s, PyString_FromString("]"));
    return s;
}

static PySequenceMethods array_as_sequence =
{
#if PY_VERSION_HEX < 0x02050000
    (inquiry)array_length,                                                    /*sq_length*/
    (binaryfunc)array_concat,                                             /*sq_concat*/
    (intargfunc)array_repeat,                                             /*sq_repeat*/
    (intargfunc)array_item,                                                 /*sq_item*/
    (intintargfunc)array_slice,                                         /*sq_slice*/
    (intobjargproc)array_ass_item,                                    /*sq_ass_item*/
    (intintobjargproc)array_ass_slice,                            /*sq_ass_slice*/
#else	
    (lenfunc)array_length,                                                    /*sq_length*/
    (binaryfunc)array_concat,                                             /*sq_concat*/
    (ssizeargfunc)array_repeat,                                             /*sq_repeat*/
    (ssizeargfunc)array_item,                                                 /*sq_item*/
    (ssizessizeargfunc)array_slice,                                         /*sq_slice*/
    (ssizeobjargproc)array_ass_item,                                    /*sq_ass_item*/
    (ssizessizeobjargproc)array_ass_slice,                            /*sq_ass_slice*/
#endif	
};

static char arraytype_doc [] =
"An array represents underlying memory of simuPOP structure \n\
so that you can edit the values in python. The type will behave \n\
very much like lists, except that you can change its size.\n\
\n\
Methods:\n\
\n\
count() -- return number of occurences of an object\n\
index() -- return index of first occurence of an object\n\
tolist() -- return the array converted to an ordinary list\n\
\n\
Variables:\n\
\n\
typecode -- the typecode character used to create the array\n\
itemsize -- the length in bytes of one array item\n\
        ";

PyTypeObject Arraytype =
{
    PyObject_HEAD_INIT(NULL)
    0,
    "simuPOP.carray",                                                             /* mudoule.type name */
    sizeof(arrayobject),
    0,
    (destructor)array_dealloc,                                            /* tp_dealloc */
    (printfunc)array_print,                                                 /* tp_print */
    (getattrfunc)array_getattr,                                         /* tp_getattr */
    0,                                                                                            /* tp_setattr */
    0,                                                                                            /* tp_compare */
    (reprfunc)array_repr,                                                     /* tp_repr */
    0,                                                                                            /* tp_as _number*/
    &array_as_sequence,                                                         /* tp_as _sequence*/
    0,                                                                                            /* tp_as _mapping*/
    0,                                                                                            /* tp_hash */
    0,                                                                                            /* tp_call */
    0,                                                                                            /* tp_str */
    0,                                                                                            /* tp_getattro */
    0,                                                                                            /* tp_setattro */
    0,                                                                                            /* tp_as_buffer*/
    Py_TPFLAGS_DEFAULT,                                                         /* tp_flags */
    arraytype_doc,                                                                    /* tp_doc */
    0,                                                                                            /* tp_traverse */
    0,                                                                                            /* tp_clear */
    array_richcompare,                                                            /* tp_richcompare */
    0,                                                                                            /* tp_weaklistoffset */
    0,                                                                                            /* tp_iter */
    0,                                                                                            /* tp_iternext */
    0,                                                                                            /* tp_methods */
    0,                                                                                            /* tp_members */
    0,                                                                                            /* tp_getset */
    0,                                                                                            /* tp_base */
    0,                                                                                            /* tp_dict */
    0,                                                                                            /* tp_descr_get */
    0,                                                                                            /* tp_descr_set */
    0,                                                                                            /* tp_dictoffset */
    (initproc)carray_init,                                                    /* tp_init */
    0,                                                                                            /* tp_alloc */
    carray_new,                                                                         /* tp_new */
};


/// CPPONLY
bool is_carrayobject(PyObject* op)
{
    return op->ob_type == &Arraytype;
}


/// CPPONLY
int carray_length(PyObject*a)
{
    return ((arrayobject*)(a))->ob_size;
}


/// CPPONLY
int carray_itemsize(PyObject*a)
{
    return ((arrayobject*)(a))->ob_descr->itemsize;
}


/// CPPONLY
char carray_type(PyObject* a)
{
    return ((arrayobject*)(a))->ob_descr->typecode;
}


/// CPPONLY
char * carray_data(PyObject*a)
{
    return ((arrayobject*)(a))->ob_iterator.ob_item;
}


/// CPPONLY
PyObject * newcarrayobject(char* ptr, char type, int size)
{
    struct arraydescr * descr;

    if (size < 0)
    {
        PyErr_BadInternalCall();
        return NULL;
    }

    // skip the first one, which is for iterator
    for (descr = descriptors+1; descr->typecode != '\0'; descr++)
    {
        if (descr->typecode == type)
        {
            // create an object and copy data
            arrayobject *op;

            op = PyObject_New(arrayobject, &Arraytype);
            if (op == NULL)
            {
                PyObject_Del(op);
                return PyErr_NoMemory();
            }
            op->ob_size = size;
            op->ob_descr = descr;
            op->ob_iterator.ob_item = ptr;
            return (PyObject *) op;
        }
    }
    PyErr_SetString(PyExc_ValueError,
        "bad typecode (must be c, b, B, h, H, i, I, l, L, f or d)");
    return NULL;
}


/// CPPONLY
PyObject * newcarrayiterobject(GenoIterator begin, GenoIterator end)
{
    // create an object and copy data
    arrayobject *op;

    op = PyObject_New(arrayobject, &Arraytype);
    if (op == NULL)
    {
        PyObject_Del(op);
        return PyErr_NoMemory();
    }
    //
    op->ob_descr = descriptors;
    op->ob_iterator.ob_iter = begin;
    op->ob_size = end - begin;
    return (PyObject *) op;
}



/* defaultdict type *********************************************************/

typedef struct {
	PyDictObject dict;
	PyObject *default_factory;
} defdictobject;

//static PyTypeObject defdict_type; /* Forward */

PyDoc_STRVAR(defdict_missing_doc,
"__missing__(key) # Called by __getitem__ for missing key; pseudo-code:\n\
  if self.default_factory is None: raise KeyError((key,))\n\
  self[key] = value = self.default_factory()\n\
  return value\n\
");

static PyObject *
defdict_missing(defdictobject *dd, PyObject *key)
{
	PyObject *factory = dd->default_factory;
	PyObject *value;
	if (factory == NULL || factory == Py_None) {
		/* XXX Call dict.__missing__(key) */
		PyObject *tup;
		tup = PyTuple_Pack(1, key);
		if (!tup) return NULL;
		PyErr_SetObject(PyExc_KeyError, tup);
		Py_DECREF(tup);
		return NULL;
	}
	value = PyEval_CallObject(factory, NULL);
	if (value == NULL)
		return value;
	if (PyObject_SetItem((PyObject *)dd, key, value) < 0) {
		Py_DECREF(value);
		return NULL;
	}
	return value;
}

PyDoc_STRVAR(defdict_copy_doc, "D.copy() -> a shallow copy of D.");

static PyObject *
defdict_copy(defdictobject *dd)
{
	/* This calls the object's class.  That only works for subclasses
	   whose class constructor has the same signature.  Subclasses that
	   define a different constructor signature must override copy().
	*/
	return PyObject_CallFunctionObjArgs((PyObject *)dd->dict.ob_type,
					    dd->default_factory, dd, NULL);
}

static PyObject *
defdict_reduce(defdictobject *dd)
{
	/* __reduce__ must return a 5-tuple as follows:

	   - factory function
	   - tuple of args for the factory function
	   - additional state (here None)
	   - sequence iterator (here None)
	   - dictionary iterator (yielding successive (key, value) pairs

	   This API is used by pickle.py and copy.py.

	   For this to be useful with pickle.py, the default_factory
	   must be picklable; e.g., None, a built-in, or a global
	   function in a module or package.

	   Both shallow and deep copying are supported, but for deep
	   copying, the default_factory must be deep-copyable; e.g. None,
	   or a built-in (functions are not copyable at this time).

	   This only works for subclasses as long as their constructor
	   signature is compatible; the first argument must be the
	   optional default_factory, defaulting to None.
	*/
	PyObject *args;
	PyObject *items;
	PyObject *result;
	if (dd->default_factory == NULL || dd->default_factory == Py_None)
		args = PyTuple_New(0);
	else
		args = PyTuple_Pack(1, dd->default_factory);
	if (args == NULL)
		return NULL;
	items = PyObject_CallMethod((PyObject *)dd, "iteritems", "()");
	if (items == NULL) {
		Py_DECREF(args);
		return NULL;
	}
	result = PyTuple_Pack(5, dd->dict.ob_type, args,
			      Py_None, Py_None, items);
	Py_DECREF(items);
	Py_DECREF(args);
	return result;
}

PyDoc_STRVAR(reduce_doc, "Return state information for pickling.");
static PyMethodDef defdict_methods[] = {
	{"__missing__", (PyCFunction)defdict_missing, METH_O,
	 defdict_missing_doc},
	{"copy", (PyCFunction)defdict_copy, METH_NOARGS,
	 defdict_copy_doc},
	{"__copy__", (PyCFunction)defdict_copy, METH_NOARGS,
	 defdict_copy_doc},
	{"__reduce__", (PyCFunction)defdict_reduce, METH_NOARGS,
	 reduce_doc},
	{NULL}
};


static PyMemberDef defdict_members[] = {
	{"default_factory", T_OBJECT,
	 offsetof(defdictobject, default_factory), 0,
	 PyDoc_STR("Factory for default value called by __missing__().")},
	{NULL}
};

static void
defdict_dealloc(defdictobject *dd)
{
	Py_CLEAR(dd->default_factory);
	PyDict_Type.tp_dealloc((PyObject *)dd);
}

static int
defdict_print(defdictobject *dd, FILE *fp, int flags)
{
	int sts;
	fprintf(fp, "defaultdict(");
	if (dd->default_factory == NULL)
		fprintf(fp, "None");
	else {
		PyObject_Print(dd->default_factory, fp, 0);
	}
	fprintf(fp, ", ");
	sts = PyDict_Type.tp_print((PyObject *)dd, fp, 0);
	fprintf(fp, ")");
	return sts;
}

static PyObject *
defdict_repr(defdictobject *dd)
{
	PyObject *defrepr;
	PyObject *baserepr;
	PyObject *result;
	baserepr = PyDict_Type.tp_repr((PyObject *)dd);
	if (baserepr == NULL)
		return NULL;
	if (dd->default_factory == NULL)
		defrepr = PyString_FromString("None");
	else
	{
		int status = Py_ReprEnter(dd->default_factory);
		if (status != 0) {
			if (status < 0)
				return NULL;
			defrepr = PyString_FromString("...");
		}
		else
			defrepr = PyObject_Repr(dd->default_factory);
		Py_ReprLeave(dd->default_factory);
	}
	if (defrepr == NULL) {
		Py_DECREF(baserepr);
		return NULL;
	}
	result = PyString_FromFormat("defaultdict(%s, %s)",
				     PyString_AS_STRING(defrepr),
				     PyString_AS_STRING(baserepr));
	Py_DECREF(defrepr);
	Py_DECREF(baserepr);
	return result;
}

static int
defdict_traverse(PyObject *self, visitproc visit, void *arg)
{
	Py_VISIT(((defdictobject *)self)->default_factory);
	return PyDict_Type.tp_traverse(self, visit, arg);
}

static int
defdict_tp_clear(defdictobject *dd)
{
	Py_CLEAR(dd->default_factory);
	return PyDict_Type.tp_clear((PyObject *)dd);
}

static int
defdict_init(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyErr_SetString(PyExc_TypeError,
        "Can not create defdict object from python.");
	return -1;
	defdictobject *dd = (defdictobject *)self;
	PyObject *olddefault = dd->default_factory;
	PyObject *newdefault = NULL;
	PyObject *newargs;
	int result;
	if (args == NULL || !PyTuple_Check(args))
		newargs = PyTuple_New(0);
	else {
		Py_ssize_t n = PyTuple_GET_SIZE(args);
		if (n > 0) {
			newdefault = PyTuple_GET_ITEM(args, 0);
			if (!PyCallable_Check(newdefault)) {
				PyErr_SetString(PyExc_TypeError,
					"first argument must be callable");                           
				return -1;
			}
		}
		newargs = PySequence_GetSlice(args, 1, n);
	}
	if (newargs == NULL)
		return -1;
	Py_XINCREF(newdefault);
	dd->default_factory = newdefault;
	result = PyDict_Type.tp_init(self, newargs, kwds);
	Py_DECREF(newargs);
	Py_XDECREF(olddefault);
	return result;
}

PyDoc_STRVAR(defdict_doc,
"defaultdict(default_factory) --> dict with default factory\n\
\n\
The default factory is called without arguments to produce\n\
a new value when a key is not present, in __getitem__ only.\n\
A defaultdict compares equal to a dict with the same items.\n\
");

/* See comment in xxsubtype.c */
#define DEFERRED_ADDRESS(ADDR) 0

static PyTypeObject defdict_type = {
	PyObject_HEAD_INIT(DEFERRED_ADDRESS(&PyType_Type))
	0,				/* ob_size */
	"collections.defaultdict",	/* tp_name */
	sizeof(defdictobject),		/* tp_basicsize */
	0,				/* tp_itemsize */
	/* methods */
	(destructor)defdict_dealloc,	/* tp_dealloc */
	(printfunc)defdict_print,	/* tp_print */
	0,				/* tp_getattr */
	0,				/* tp_setattr */
	0,				/* tp_compare */
	(reprfunc)defdict_repr,		/* tp_repr */
	0,				/* tp_as_number */
	0,				/* tp_as_sequence */
	0,				/* tp_as_mapping */
	0,	       			/* tp_hash */
	0,				/* tp_call */
	0,				/* tp_str */
	PyObject_GenericGetAttr,	/* tp_getattro */
	0,				/* tp_setattro */
	0,				/* tp_as_buffer */
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC |
		Py_TPFLAGS_HAVE_WEAKREFS,	/* tp_flags */
	defdict_doc,			/* tp_doc */
	defdict_traverse,		/* tp_traverse */
	(inquiry)defdict_tp_clear,	/* tp_clear */
	0,				/* tp_richcompare */
	0,				/* tp_weaklistoffset*/
	0,				/* tp_iter */
	0,				/* tp_iternext */
	defdict_methods,		/* tp_methods */
	defdict_members,		/* tp_members */
	0,				/* tp_getset */
	DEFERRED_ADDRESS(&PyDict_Type),	/* tp_base */
	0,				/* tp_dict */
	0,				/* tp_descr_get */
	0,				/* tp_descr_set */
	0,				/* tp_dictoffset */
	defdict_init,			/* tp_init */
	PyType_GenericAlloc,		/* tp_alloc */
	0,				/* tp_new */
	PyObject_GC_Del,		/* tp_free */
};

PyObject * PyDefDict_New()
{
	defdictobject * obj;

	// This is almost a hack, but I do not know how to create a defdict
	// object that calls dict_new properly.
	obj = (defdictobject*)PyDict_Type.tp_new((PyTypeObject*)(&defdict_type), NULL, NULL);
	if (obj == NULL)
	{
		PyObject_Del(obj);
		return PyErr_NoMemory();
	}
	// initialize this object (call PyDict_Type.tp_init)
	Py_INCREF(&PyInt_Type);
	PyObject * args = PyTuple_New(0);
	defdict_init((PyObject*)obj, args, NULL);
	Py_DECREF(args);
	// set default factory.
	obj->default_factory = (PyObject*)(&PyInt_Type);
	return (PyObject*)obj;
}


bool is_defdict(PyTypeObject * type)
{
	return type == &defdict_type;
}

// we do not import or export hings,
// carray is defined within simuPOP.
/// CPPONLY
int initcarray(void)
{
    // this will be done in PyType_Ready() is your read this
    // from python reference manual.
    Arraytype.ob_type = &PyType_Type;
	if (PyType_Ready(&Arraytype) < 0)
		return -1;
	//
    defdict_type.ob_type = &PyType_Type;
	defdict_type.tp_base = &PyDict_Type;
	if (PyType_Ready(&defdict_type) < 0)
		return -1;
	//Py_INCREF(&defdict_type);
	return 0;
}

