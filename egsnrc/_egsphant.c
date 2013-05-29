/* $Id: _egsphant.c 115 2008-01-16 17:34:05Z dwchin $ */

#ifndef lint
static char vcid[] = "$Id: _egsphant.c 115 2008-01-16 17:34:05Z dwchin $";
#endif /* lint */

/* _egsphant.c       2006-05-18 19:13UTC
 *
 * A module for reading egsphant files produced by DOSXYZnrc
 *
 * Based heavily on TableIO by Michael A. Miller <mmiller@debian.org>
 * with much poorer error-handling abilities.
 *
 * The egsphant file format is documented here:
 *   http://www.irs.inms.nrc.ca/BEAM/user_manuals/pirs794/node95.html
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
    { fclose(phantfile); PyErr_SetString(ErrorObject, message); return NULL; }

#define decrefAll() \
    { Py_XDECREF(materialsList); Py_XDECREF(estepeList); \
        Py_XDECREF(dimensionsTuple); Py_XDECREF(xedgesList); \
        Py_XDECREF(yedgesList); Py_XDECREF(zedgesList); \
        Py_XDECREF(xList); Py_XDECREF(yList); Py_XDECREF(zList); \
        Py_XDECREF(materialscanList); Py_XDECREF(densityscanList); }

/*
 * Exported module method-functions
 * This is a translation and conglomeration of the original Python methods
 * in EGSPhant.py. The code there is commented out, but it will probably
 * make more sense than the C here.
 */

static PyObject *
egsphant_read(PyObject *self, PyObject *args)
{
    /* reads materials info; takes PyFileObject as argument */

    char *phantfilename = NULL;
    FILE *phantfile = NULL;      /* egsphant file pointer */
    int i, j, k;

    int nmaterials = 0;
    char   material[256];
    double estepe = 0.;
    int xdim, ydim, zdim;
    double tmpdata1 = 0.;
    double tmpdata2 = 0.;
    char   material_id = '\0';
    char   material_line[2048];
    double density = 0.;
    
    PyObject *myDict = NULL;  /* dictionary to be returned */
    PyObject *materialsList = NULL; /* list of materials */
    PyObject *estepeList = NULL;    /* list of estepe values */
    PyObject *dimensionsTuple = NULL;
    PyObject *xedgesList = NULL;  /* lists of voxel edges */
    PyObject *yedgesList = NULL;
    PyObject *zedgesList = NULL;
    PyObject *xList = NULL;     /* lists of voxel centers */
    PyObject *yList = NULL;
    PyObject *zList = NULL;
    PyObject *materialscanList = NULL;
    PyObject *densityscanList = NULL;
    
    int status;        /* status flag */

    char *key; /* dictionary key */
    
    if (debug_p) 
    {
        printf("%s\n", vcid);
        printf("CUBAAN: %d\n", __LINE__);
    }

    /*
     * Check args: need filename
     */
    if (!PyArg_ParseTuple(args, "s", &phantfilename))
        return NULL;

    if (debug_p)
        printf("CUBAAN: %d\n", __LINE__);

    /* Check that input egsphant file is readable */
    phantfile = fopen(phantfilename, "r");
    if (phantfile == NULL) 
    {
        onError("Error opening input file");
    }
    
    if (debug_p)
        printf("CUBAAN: %d\n", __LINE__);
         

    /*
     * construct objects
     */
    myDict = PyDict_New();
    dimensionsTuple = PyTuple_New(3);
    
    if (debug_p)
        printf("CUBAAN: %d\n", __LINE__);

    /* read number of materials */
    fscanf(phantfile, "%d", &nmaterials);
    
    if (debug_p)
        printf("CUBAAN: %d: nmaterials = %d\n", __LINE__, nmaterials);

    key = "nmaterials";
    status = PyDict_SetItemString(myDict, key, Py_BuildValue("i", nmaterials));
    if (status)
    {
        decrefAll();
        Py_XDECREF(myDict);
        onError("Error adding nmaterials to dictionary");
    }
    
    if (debug_p)
        printf("CUBAAN: %d\n", __LINE__);

    /* read list of materials (each is a string), and 
     * add them to the materials list */
    materialsList = PyList_New(nmaterials);
    for (i = 0; i < nmaterials; ++i)
    {
        fscanf(phantfile, "%s ", material);
        
        if (debug_p)
            printf("CUBAAN: %d: i = %d,  material = %s\n", __LINE__, i, material);

        PyList_SET_ITEM(materialsList, i, Py_BuildValue("s", material));
    }

    key = "materials";
    status = PyDict_SetItemString(myDict, key, materialsList);
    if (status)
    {
        decrefAll();
        Py_XDECREF(myDict);
        onError("Error adding materials to dictionary");
    }

    if (debug_p)
        printf("CUBAAN: %d\n", __LINE__);

    /* read list of estepe values */
    estepeList = PyList_New(nmaterials);
    for (i = 0; i < nmaterials; ++i)
    {
        fscanf(phantfile, "%lf", &estepe);

        PyList_SET_ITEM(estepeList, i, Py_BuildValue("d", estepe));
    }
    
    key = "estepe";
    status = PyDict_SetItemString(myDict, key, estepeList);
    if (status)
    {
        decrefAll();
        Py_XDECREF(myDict);
        onError("Error adding estepe to dictionary");
    }
    
    if (debug_p)
        printf("CUBAAN: %d\n", __LINE__);
    
    /*
     * read dimensions
     */
    fscanf(phantfile, "%d %d %d", &xdim, &ydim, &zdim);
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
        printf("CUBAAN: %d\n", __LINE__);

    /*
     * read voxel edges
     */

    /* x edges and centers */
    xedgesList = PyList_New(xdim+1);
    xList = PyList_New(xdim);
    for (i = 0; i < xdim+1; ++i)
    {
        fscanf(phantfile, "%lf", &tmpdata1);
        PyList_SET_ITEM(xedgesList, i, Py_BuildValue("d", tmpdata1));
        
        /* centers */
        if (i > 0)
        {
            PyList_SET_ITEM(xList, i-1, Py_BuildValue("d", (tmpdata1+tmpdata2)/2.));
        }
        
        /* keep previous point */
        tmpdata2 = tmpdata1;
    }

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

    /* y edges and centers */
    yedgesList = PyList_New(ydim+1);
    yList = PyList_New(ydim);
    for (i = 0; i < ydim+1; ++i)
    {
        fscanf(phantfile, "%lf", &tmpdata1);
        PyList_SET_ITEM(yedgesList, i, Py_BuildValue("d", tmpdata1));
        
        /* centers */
        if (i > 0)
        {
            PyList_SET_ITEM(yList, i-1, Py_BuildValue("d", (tmpdata1+tmpdata2)/2.));
        }
        
        /* keep previous point */
        tmpdata2 = tmpdata1;
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
    
    /* z edges and centers */
    zedgesList = PyList_New(zdim+1);
    zList = PyList_New(zdim);
    for (i = 0; i < zdim+1; ++i)
    {
        fscanf(phantfile, "%lf", &tmpdata1);
        PyList_SET_ITEM(zedgesList, i, Py_BuildValue("d", tmpdata1));
        
        /* centers */
        if (i > 0)
        {
            PyList_SET_ITEM(zList, i-1, Py_BuildValue("d", (tmpdata1+tmpdata2)/2.));
        }
        
        /* keep previous point */
        tmpdata2 = tmpdata1;
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
        printf("CUBAAN: %d\n", __LINE__);
    
    /*
     * Read in materialscan
     *   this goes into a flat list, so it will need to be 
     *   reshaped with the numarray array() factory
     */
    materialscanList = PyList_New(xdim*ydim*zdim);
    for (k = 0; k < zdim; ++k)
    {
        for (j = 0; j < ydim; ++j)
        {
            fscanf(phantfile, "%s ", material_line);
            
            for (i = 0; i < xdim; ++i)
            {
                if (debug_p)
                    printf("YOWZA: line no. %d; material_line[%d] = %c\n",
                           __LINE__, i, material_line[i]);
                
                material_id = material_line[i];

                if (debug_p)
                    printf("ARRGH: line no. %d; material_id = %c\n", __LINE__, material_id);
                
                PyList_SET_ITEM(materialscanList, k*ydim*xdim + j*xdim + i,
                                Py_BuildValue("i", atoi(&material_id)));
            }
        }
    }

    key = "materialscan";
    status = PyDict_SetItemString(myDict, key, materialscanList);
    
    if (debug_p)
        printf("CUBAAN: %d\n", __LINE__);
    
    /*
     * Read in densityscan
     *   this goes into a flat list, so it will need to be 
     *   reshaped with the numarray array() factory
     */
    densityscanList = PyList_New(xdim*ydim*zdim); 
    for (k = 0; k < zdim; ++k)
    {
        for (j = 0; j < ydim; ++j)
        {
            for (i = 0; i < xdim; ++i)
            {
                fscanf(phantfile, "%le ", &density);
                PyList_SET_ITEM(densityscanList, k*ydim*xdim + j*xdim + i,
                                Py_BuildValue("d", density));
            }
        }
    }

    key = "densityscan";
    status = PyDict_SetItemString(myDict, key, densityscanList);
    
    if (debug_p)
        printf("CUBAAN: %d\n", __LINE__);
    
    if (status)
    {
        decrefAll();
        Py_XDECREF(myDict);
        onError("Error adding densityscan to dictionary");
    }

    /*
     * Housekeeping
     */
    decrefAll();

    return (PyObject *)myDict;
}


/* 
 * Method registration table
 */
static struct PyMethodDef
egsphant_methods[] = {
    {"read", egsphant_read, 1},
    {NULL,   NULL}
};

/*
 * Initialization
 */
void
init_egsphant(void)
{
    PyObject *m, *d;
    
    /* create this module and add functions */
    m = Py_InitModule("_egsphant", egsphant_methods);
    
    /* add symbolic constants to this moduse */
    d = PyModule_GetDict(m);
    ErrorObject = Py_BuildValue("s", "egsphant.error");
    PyDict_SetItemString(d, "error", ErrorObject);
    
    /* check for errors */
    if (PyErr_Occurred())
    {
        Py_FatalError("Could not initialize module _egsphant");
    }
}
