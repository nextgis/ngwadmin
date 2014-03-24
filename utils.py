# -*- coding: utf-8 -*-

"""
***************************************************************************
    utils.py
    ---------------------
    Date                 : March 2014
    Copyright            : (C) 2014 by NextGIS
    Email                : info at nextgis dot org
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = 'NextGIS'
__date__ = 'March 2014'
__copyright__ = '(C) 2014, NextGIS'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import json
import uuid
import zipfile

import requests

from PyQt4.QtCore import *
from qgis.core import *

def tempFileName():
    fName = os.path.join(QDir.tempPath(), str(uuid.uuid4()).replace('-', '') + '.zip')
    return fName

def getMapLayers():
    layerMap = QgsMapLayerRegistry.instance().mapLayers()
    layers = dict()
    for name, layer in layerMap.iteritems():
        if layer.type() == QgsMapLayer.VectorLayer:
            if layer.storageType() == 'ESRI Shapefile' or layer.providerType() == 'postgres':
                if layer.id() not in layers.keys():
                    layers[layer.id()] = unicode(layer.name())
    return layers

def getLayerById(layerId):
    layerMap = QgsMapLayerRegistry.instance().mapLayers()
    for name, layer in layerMap.iteritems():
        if layer.id() == layerId:
            if layer.isValid():
                return layer
            else:
                return None

def getResourceGroups(url, auth):
    res = requests.get(url + '/resource/0/child/', auth=auth)

    if res.status_code != 200:
        return None

    groups = dict()
    groups[0] = '<root group>'
    for i in xrange(len(res.json())):
        item = res.json()[i]['resource']
        if item['cls'] == 'resource_group':
            groups[item['id']] = item['display_name']

    return groups

def addResourceGroup(url, auth, parent, name):
    url = url + '/resource/' + str(parent) + '/child/'
    params = dict(resource=dict(cls='resource_group', display_name=name))
    res = requests.post(url, auth=auth, data=json.dumps(params))

def uploadShapeLayer(url, auth, group, layer, name):
    tmp = tempFileName()
    src = layer.source()
    basePath = os.path.splitext(src)[0]
    baseName = os.path.splitext(os.path.basename(src))[0]

    zf = zipfile.ZipFile(tmp, "w")
    for i in ['.shp', '.shx', '.dbf']:
        zf.write(basePath + i, baseName + i)
    wkt = layer.dataProvider().crs().toWkt()
    zf.writestr(baseName + '.prj', wkt)
    zf.close()

    with open(tmp, 'rb') as f:
        vl = requests.put(url + '/file_upload/upload', auth=auth, data=f)

    crs = dict(id=3857)
    params = dict(resource=dict(cls='vector_layer', display_name=name), vector_layer=dict(srs=crs, source=vl.json()))
    url = url + '/resource/' + str(group) + '/child/'
    res = requests.post(url, auth=auth, data=json.dumps(params))

def uploadPostgisLayer(url, auth, group, layer, name):
    pass
