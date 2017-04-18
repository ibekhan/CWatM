#-------------------------------------------------------------------------------
# Name:        routing_sub
# Purpose:     subroutines for routing kinematic waves
#
# Author:      burekpe
#
# Created:     17/01/2017
# Copyright:   (c) burek 2017
#-------------------------------------------------------------------------------


import numpy as np
import math
from management_modules.data_handling import *



"""
ROUTING subroutines
partly using C++ for speeding up
"""


def Compress (map,mask):
    """
    compressing map from 2D to 1D without missing values
    :param map:  input map
    :param mask: mask map
    :return: compressed map
    """
    maskmap = np.ma.masked_array(map,mask)
    compmap = np.ma.compressed(maskmap)
    return compmap


def Decompress(compmap,mask,emptymap):
    """
    Decompressing map from 1D to 2D with missing values
    :param compmap: compressed map
    :param mask:  mask map
    :param emptymap: map with only 0 in
    :return: decompressed 2D map
    """
    dmap=emptymap.copy()
    dmap[~mask.ravel()] = compmap[:]
    dmap = dmap.reshape(mask.shape)
    return dmap


def decompress1(map):
    """
    redundant have to look if it is still used

    Todo:
        remove it?

    :param map:
    :return:
    """
    dmap = maskinfo['maskall'].copy()
    dmap[~maskinfo['maskflat']] = map[:]
    dmap = dmap.reshape(maskinfo['shape'])
    return dmap




def postorder(dirUp,catchment,node,catch,dirDown):
    """
    routine to run a postoder tree traversal
    :param dirUp:
    :param catchment:
    :param node:
    :param catch:
    :param dirDown:
    :return: dirDown and catchment
    """

    if dirUp[node] != []:
        postorder(dirUp,catchment,dirUp[node][0],catch,dirDown)
        catchment[dirUp[node][0]]=catch
        dirDown.append(dirUp[node][0])
        if len(dirUp[node])>1:
            postorder(dirUp,catchment,dirUp[node][1],catch,dirDown)
            catchment[dirUp[node][1]]=catch
            dirDown.append(dirUp[node][1])
            if len(dirUp[node])>2:
               postorder(dirUp,catchment,dirUp[node][2],catch,dirDown)
               catchment[dirUp[node][2]]=catch
               dirDown.append(dirUp[node][2])
               if len(dirUp[node])>3:
                postorder(dirUp,catchment,dirUp[node][3],catch,dirDown)
                catchment[dirUp[node][3]]=catch
                dirDown.append(dirUp[node][3])
                if len(dirUp[node])>4:
                 postorder(dirUp,catchment,dirUp[node][4],catch,dirDown)
                 catchment[dirUp[node][4]]=catch
                 dirDown.append(dirUp[node][4])
                 if len(dirUp[node])>5:
                  postorder(dirUp,catchment,dirUp[node][5],catch,dirDown)
                  catchment[dirUp[node][5]]=catch
                  dirDown.append(dirUp[node][5])
                  if len(dirUp[node])>6:
                   postorder(dirUp,catchment,dirUp[node][6],catch,dirDown)
                   catchment[dirUp[node][6]]=catch
                   dirDown.append(dirUp[node][6])
                   if len(dirUp[node])>7:
                    postorder(dirUp,catchment,dirUp[node][7],catch,dirDown)
                    catchment[dirUp[node][7]]=catch
                    dirDown.append(dirUp[node][7])


def dirUpstream(dirshort):
    """
    runs the network tree upstream from outlet to source

    :param dirshort:
    :return:
    """

    # -- up direction
    dirUp = list([] for i in xrange(maskinfo['mapC'][0]))
    for i in xrange(dirshort.shape[0]):
        value=dirshort[i]
        if value > -1:
           dirUp[value].append(i)

    dirupLen=[0]
    dirupID=[]
    j = 0
    for i in xrange(dirshort.shape[0]):
        j += len(dirUp[i])
        dirupLen.append(j)
        for k in xrange(len(dirUp[i])):
            dirupID.append(dirUp[i][k])

    return dirUp,np.array(dirupLen).astype(np.int64),np.array(dirupID).astype(np.int64)


def dirDownstream(dirUp,lddcomp,dirDown):
    """
    runs the river network tree downstream - from source to outlet

    :param dirUp:
    :param lddcomp:
    :param dirDown:
    :return:
    """

    catchment = np.array(np.zeros(maskinfo['mapC'][0]), dtype=np.int64)
    j=0
    for pit in xrange(maskinfo['mapC'][0]):
        if lddcomp[pit]==5:
            j+=1
            postorder(dirUp,catchment,pit,j,dirDown)
            dirDown.append(pit)
            catchment[pit]=j
    return np.array(dirDown).astype(np.int64),np.array(catchment).astype(np.int64)



def upstreamArea(dirDown,dirshort,area):
    """
    calculates upstream area
    :param dirDown: array which point from each cell to the next downstream cell
    :param dirshort:
    :param area: area in m2 for a single gridcell
    :return:
    """

    ups = area.copy()
    lib2.ups(dirDown,dirshort, ups,len(dirDown))
    return ups

def upstream1(downstruct, weight):
    """
    Calculates 1 cell upstream

    :param downstruct:
    :param weight:
    :return:
    """
    return np.bincount(downstruct, weights=weight)[:-1]


def downstream1(dirUp,weight):
    """
    calculated 1 cell downstream

    :param dirUp:
    :param weight:
    :return:
    """

    downstream = weight.copy()
    k = 0
    for i in dirUp:
        for j in i:
           downstream[j]=weight[k]
        k += 1
    return downstream


def catchment1(dirUp, points):
    """
    calculates all cells which belongs to a catchment from point onward

    :param dirUp:
    :param points:
    :return:
    """

    subcatch = np.array(np.zeros(maskinfo['mapC'][0]), dtype=np.int64)
    # if subcatchment = true ->  calculation of subcatchment: every point is calculated
    # if false : calculation of catchment: only point calculated which are not inside a bigger catchment from another point


    for cell in xrange(maskinfo['mapC'][0]):
        j = points[cell]
        if (j > 0) and (subcatch[cell] < 1):
            dirDown =[]
            postorder(dirUp, subcatch, cell, j,dirDown)
            subcatch[cell] = j
    return subcatch



def subcatchment1(dirUp, points,ups):
    """
    calculates subcatchments of points

    :param dirUp:
    :param points:
    :param ups:
    :return:
    """

    subcatch = np.array(np.zeros(maskinfo['mapC'][0]), dtype=np.int64)
    # if subcatchment = true ->  calculation of subcatchment: every point is calculated
    # if false : calculation of catchment: only point calculated which are not inside a bigger catchment from another point

    subs = {}
    #sort waterbodies of reverse upstream area
    for cell in xrange(maskinfo['mapC'][0]):
        if points[cell] > 0:
            subs[points[cell]] = [cell, ups[cell]]
    subsort = sorted(subs.items(), key=lambda x: x[1][1], reverse=True)


    #for cell in xrange(maskinfo['mapC'][0]):
    for sub in subsort:
        j = sub[0]
        cell = sub[1][0]
        dirDown=[]
        postorder(dirUp, subcatch, cell, j,dirDown)
        subcatch[cell] = j

    return subcatch


# ----------------------------------------------------------------



def defLdd2(ldd):
    """
    defines river network

    :param ldd:
    :return:
    """

    ldd2D = decompress(ldd, pcr1=False).astype(np.int64)
    ldd2D[ldd2D.mask] = 0

    # every cell gets an order starting from 0 ...
    lddshortOrder =np.arange(maskinfo['mapC'][0])
    # decompress this map to 2D
    lddOrder = decompress1(lddshortOrder)
    lddOrder[maskinfo['mask']]=-1
    lddOrder = np.array(lddOrder.data, dtype=np.int64)


    lddCompress, dirshort = lddrepair(ldd2D, lddOrder)
    dirUp, dirupLen, dirupID = dirUpstream(dirshort)

    # for upstream calculation
    inAr = np.arange(maskinfo['mapC'][0], dtype=np.int64)
    # each upstream pixel gets the id of the downstream pixel
    downstruct = downstream1(dirUp, inAr).astype(np.int64)
    # all pits gets a high number
    downstruct[lddCompress == 5] = maskinfo['mapC'][0]

    # self.var.dirDown: direction downstream - from each cell the pointer to a downstream cell (can only be 1)
    # self.var.catchment: each catchment with a pit gets a own ID
    dirDown = []
    dirDown, catchment = dirDownstream(dirUp, lddCompress,dirDown)
    lendirDown = len(dirDown)

    return lddCompress, dirshort, dirUp, dirupLen, dirupID, downstruct, catchment, dirDown, lendirDown



def lddrepair(lddnp,lddOrder):
    """
    repairs a river network

    * eliminate unsound parts
    * add pits at points with no connections

    :param lddnp:
    :param lddOrder:
    :return:
    """

    yi=lddnp.shape[0]
    xi=lddnp.shape[1]
    #print "========= repair 1"

    # direction downstream naming the order of the cell
    dir = np.array(np.empty(maskinfo['shape']), dtype=np.int64)
    dir.fill(-1)

    lib2.repairLdd1(lddnp, yi,xi)

    lddcomp = compressArray(lddnp, pcr=False).astype(np.int64)
    lib2.dirID(lddOrder, lddnp, dir,yi,xi)
    dirshort = compressArray(dir, pcr=False).astype(np.int64)

    check = np.array(np.zeros(maskinfo['mapC'][0]),dtype=np.int64)
    lib2.repairLdd2(lddcomp, dirshort, check,maskinfo['mapC'][0] )

	
	
	
    """
    for i in xrange(maskattr["compshape"]):
       path=[]
       j=i
       while 1:
          if j in path:
            lddcomp[path[-1]] = 5
            dirshort[path[-1]] = -1
            break
          if (lddcomp[j]==5) or (check[j]==1): break
          path.append(j)
          j = dirshort[j]
       check[path]=1
    """

    return lddcomp, dirshort
