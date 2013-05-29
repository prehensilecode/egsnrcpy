/* $Id: _mcdose.c 115 2008-01-16 17:34:05Z dwchin $ */

#ifndef lint
static char vcid[] = "$Id: _mcdose.c 115 2008-01-16 17:34:05Z dwchin $";
#endif /* lint */

/* _mcdose.c       2005-12-20 00:59 UTC
 *
 * A module for reading 3ddose files produced by DOSXYZnrc
 *
 * Based heavily on TableIO by Michael A. Miller <mmiller@debian.org>
 * with much poorer error-handling abilities.
 *
 * The 3ddose file format is documented here:
 *    http://www.irs.inms.nrc.ca/BEAM/user_manuals/statdose/node12.html
 *
 * Copyright -- TBA
 *    FIXME check BWH & Harvard's policy on IP.
 */
 
#include "Python.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>


static PyObject *ErrorObject;    /* locally-raised exception */

static int debug_p = 0;

#define onError(message) \
    { fclose(infile); PyErr_SetString(ErrorObject, message); return NULL; }
    
/* Because 'result' may be NULL, not a PyObject*, we must call PyXDECREF not Py_DECREF */
#define decrefAll() \
    { Py_XDECREF(dimensionsTuple); Py_XDECREF(xedgesList); \
      Py_XDECREF(yedgesList); Py_XDECREF(zedgesList); \
      Py_XDECREF(xList); Py_XDECREF(yList); Py_XDECREF(zList); \
      Py_XDECREF(doseList); Py_XDECREF(errorList); }
    
    
/*
 * Exported module method-functions
 * See the commented-out read() method in MCDose.py
 * as a reference implementation. This C function is
 * supposed to duplicate that method.
 */
static PyObject *
mcdose_read(PyObject *self, PyObject *args)
{
    char *filename;    /* name of .3ddose file */
    FILE *infile;      /* 3ddose file pointer */
    int i, j, k;
    
    int xdim, ydim, zdim;
    double tmpdata = 0.;    /* temporary variables for input */
    double tmpdata2 = 0.;
    
    int status;        /* status flag */
    
    PyObject *myDict = NULL;  /* dictionary to be returned */
    PyObject *dimensionsTuple = NULL; /* list for storing dimensions of the dose distribution */
    PyObject *xedgesList = NULL; /* lists for x, y, and z voxel edges */
    PyObject *yedgesList = NULL;
    PyObject *zedgesList = NULL;
    PyObject *xList = NULL; /* lists for x, y, and z voxel centers */
    PyObject *yList = NULL;
    PyObject *zList = NULL;
    PyObject *doseList = NULL;  /* list for storing read data */
    PyObject *errorList = NULL; /* list for storing errors */
    
    char *key;     /* dictionary key */
    
    if (debug_p)
        printf("%s\n", vcid);
    
    
    /*
     * Check arguments:
     *     need filename
     */
    if (!PyArg_ParseTuple(args, "s", &filename))
        return NULL;
    
    /* Check that input 3ddose file is readable */
    infile = fopen(filename, "r");
    if (infile == NULL) 
    {
        onError("Error opening input file");
    }
    
    /* 
     * construct new dictionary
     */
    myDict = PyDict_New();
    
    /* read in dimensions */
    fscanf(infile, "%d %d %d\n", &xdim, &ydim, &zdim);
    
    if (debug_p)
        printf("xdim = %d; ydim = %d; zdim = %d\n", xdim, ydim, zdim);
    
    dimensionsTuple = PyTuple_New(3);
    PyTuple_SET_ITEM(dimensionsTuple, 0, Py_BuildValue("i", xdim));
    PyTuple_SET_ITEM(dimensionsTuple, 1, Py_BuildValue("i", ydim));
    PyTuple_SET_ITEM(dimensionsTuple, 2, Py_BuildValue("i", zdim));
    
    
    key = "dimensions";
    status = PyDict_SetItemString(myDict, key, dimensionsTuple);
    
    if (status)
    {
        decrefAll();
        Py_XDECREF(myDict);
        onError("Error adding dimensions to dictionary");
    }
    
    if (debug_p)
        printf("aloha: %d\n", __LINE__);
    
    /* 
     * read in edges, and compute centers
     */

    /* x edges, and centers */
    xedgesList = PyList_New(0);
    xList      = PyList_New(0);
    
    for (i = 0; i < xdim+1; ++i)
    {
        fscanf(infile, "%lf", &tmpdata);
        status = PyList_Append(xedgesList, Py_BuildValue("d", tmpdata));

        if (status)
        {
            decrefAll();
            Py_XDECREF(myDict);
            onError("Error reading x edges");
        }

        if (i > 0)
        {
            status = PyList_Append(xList, 
                                   Py_BuildValue("d", (tmpdata + tmpdata2)/2.));

            if (status)
            {
                decrefAll();
                Py_XDECREF(myDict);
                onError("Error computing x centers");
            }
        }

        tmpdata2 = tmpdata;
    }
    
    if (debug_p)
        printf("aloha: %d\n", __LINE__);
    
    key = "xedges";
    status = PyDict_SetItemString(myDict, key, xedgesList);
    
    if (status)
    {
        decrefAll();
        Py_XDECREF(myDict);
        onError("Error adding x edges to dictionary");
    }
    
    key = "x";
    status = PyDict_SetItemString(myDict, key, xList);

    if (status)
    {
        decrefAll();
        Py_XDECREF(myDict);
        onError("Error adding x centers to dictionary");
    }
    
    /* y edges, and centers */
    yedgesList = PyList_New(0);
    yList      = PyList_New(0);
    
    for (i = 0; i < ydim+1; ++i)
    {
        fscanf(infile, "%lf", &tmpdata);
        status = PyList_Append(yedgesList, Py_BuildValue("d", tmpdata));
        
        if (status)
        {
            decrefAll();
            Py_XDECREF(myDict);
            onError("Error reading y edges");
        }

        if (i > 0)
        {
            status = PyList_Append(yList, 
                                   Py_BuildValue("d", (tmpdata + tmpdata2)/2.));

            if (status)
            {
                decrefAll();
                Py_XDECREF(myDict);
                onError("Error computing y centers");
            }
        }

        tmpdata2 = tmpdata;
    }
    
    key = "yedges";
    status = PyDict_SetItemString(myDict, key, yedgesList);
    
    if (status)
    {
        decrefAll();
        Py_XDECREF(myDict);
        onError("Error adding y edges to dictionary");
    }
    
    key = "y";
    status = PyDict_SetItemString(myDict, key, yList);

    if (status)
    {
        decrefAll();
        Py_XDECREF(myDict);
        onError("Error adding y centers to dictionary");
    }
    
    
    /* z edges, and centers */
    zedgesList = PyList_New(0);
    zList      = PyList_New(0);
    
    for (i = 0; i < zdim+1; ++i)
    {
        fscanf(infile, "%lf", &tmpdata);
        status = PyList_Append(zedgesList, Py_BuildValue("d", tmpdata));
        
        if (status)
        {
            decrefAll();
            Py_XDECREF(myDict);
            onError("Error reading z edges");
        }

        if (i > 0)
        {
            status = PyList_Append(zList, 
                                   Py_BuildValue("d", (tmpdata + tmpdata2)/2.));

            if (status)
            {
                decrefAll();
                Py_XDECREF(myDict);
                onError("Error computing z centers");
            }
        }

        tmpdata2 = tmpdata;
    }
    
    key = "zedges";
    status = PyDict_SetItemString(myDict, key, zedgesList);
    
    if (status)
    {
        decrefAll();
        Py_XDECREF(myDict);
        onError("Error adding z edges to dictionary");
    }

    key = "z";
    status = PyDict_SetItemString(myDict, key, zList);

    if (status)
    {
        decrefAll();
        Py_XDECREF(myDict);
        onError("Error adding z centers to dictionary");
    }

    if (debug_p)
        printf("aloha: %d\n", __LINE__);

    /*
     * Read in dose distribution
     *   this goes into a flat list, so it will need to be 
     *   reshaped with the numarray array() factory
     */
    doseList = PyList_New(0);
    
    for (k = 0; k < zdim; ++k)
    {
        for (j = 0; j < ydim; ++j)
        {
            for (i = 0; i < xdim; ++i)
            {
                fscanf(infile, "%le", &tmpdata);
                status = PyList_Append(doseList, 
                                       Py_BuildValue("d", tmpdata));

                if (status)
                {
                    decrefAll();
                    onError("Error reading dose values");
                }
            }
        }
    }

    key = "dose";
    status = PyDict_SetItemString(myDict, key, doseList);
    
    if (status)
    {
        decrefAll();
        Py_XDECREF(myDict);
        onError("Error adding dose to dictionary");
    }
    
    if (debug_p)
        printf("aloha: %d\n", __LINE__);
    
    /*
     * Read in error distribution
     * XXX: is it possible to deal with dose files that don't 
     * contain the error matrix?
     */
    errorList = PyList_New(0);
    
    for (k = 0; k < zdim; ++k)
    {
        for (j = 0; j < ydim; ++j)
        {
            for (i = 0; i < xdim; ++i)
            {
                fscanf(infile, "%lf", &tmpdata);
                status = PyList_Append(errorList, 
                                       Py_BuildValue("d", tmpdata));

                if (status)
                {
                    decrefAll();
                    Py_XDECREF(myDict);
                    onError("Error reading error values");
                }
            }
        }
    }

    key = "error";
    status = PyDict_SetItemString(myDict, key, errorList);
    
    if (status)
    {
        decrefAll();
        Py_XDECREF(myDict);
        onError("Error adding error array to dictionary");
    }
    
    if (debug_p)
        printf("aloha: %d\n", __LINE__);
    
    /*
     * Housekeeping
     */
    fclose(infile);

    /* done with the data members, so can decref them */
    decrefAll();
    
    if (debug_p)
        printf("aloha: %d\n", __LINE__);
    
    return (PyObject *)myDict;
} /* END: mcdose_readMCDose() */

/* 
 * Method registration table
 */
static struct PyMethodDef
mcdose_methods[] = {
    {"read", mcdose_read, 1},
    {NULL,   NULL}
};

/*
 * Initialization
 */
void
init_mcdose(void)
{
    PyObject *m, *d;
    
    /* create this module and add functions */
    m = Py_InitModule("_mcdose", mcdose_methods);
    
    /* add symbolic constants to this moduse */
    d = PyModule_GetDict(m);
    ErrorObject = Py_BuildValue("s", "mcdose.error");
    PyDict_SetItemString(d, "error", ErrorObject);
    
    /* check for errors */
    if (PyErr_Occurred())
    {
        Py_FatalError("Could not initialize module _mcdose");
    }
}
