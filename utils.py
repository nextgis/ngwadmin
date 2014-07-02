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
import re
import json
import uuid
import zipfile
import datetime

import requests

from PyQt4.QtCore import *
from qgis.core import *

class NGWError(Exception):
    def __init__(self, message, code=None):
        self.message = unicode(message, 'utf-8')
        self.status_code = (unicode(code) if code is not None else None)

    def __str__(self):
        return 'STATUS CODE: %s\nMESSAGE: %s' % (self.status_code, self.message)

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
    try:
        res = requests.get(url + '/resource/0/child/', auth=auth)
    except requests.exceptions.RequestException, e:
        raise NGWError(e.message)

    if res.status_code != 200:
        raise NGWError('Cannot get list of resource groups', res.status_code)

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
    try:
        res = requests.post(url, auth=auth, data=json.dumps(params))
        if res.status_code not in [200, 201]:
            raise NGWError(
                'Cannot create resource. Server responce:\n\n%s' % res.content,
                 res.status_code)
    except requests.exceptions.RequestException, e:
         raise NGWError(e.message)


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
        try:
            vl = requests.put(url + '/file_upload/upload', auth=auth, data=f)
            if vl.status_code != 201:
                raise NGWError(
                    'Cannot create resource. Server responce:\n\n%s' % vl.content,
                     vl.status_code)
        except requests.exceptions.RequestException, e:
            raise NGWError(e.message)

    crs = dict(id=3857)
    params = dict(resource=dict(cls='vector_layer', display_name=name), vector_layer=dict(srs=crs, source=vl.json()))
    url = url + '/resource/' + str(group) + '/child/'
    try:
        res = requests.post(url, auth=auth, data=json.dumps(params))
        if res.status_code != 200:
            raise NGWError('Request failed. Server responce:\n\n%s' % res.content,
                     res.status_code)
    except requests.exceptions.RequestException, e:
        raise NGWError(e.message)


def uploadPostgisLayer(url, auth, group, layer, name):
    metadata = layer.source().split(' ')

    regex = re.compile("^host=.*")
    pos = metadata.index([m.group(0) for l in metadata for m in [regex.search(l)] if m][0])
    tmp = metadata[pos]
    pos = tmp.find("=")
    host = tmp[pos + 1:]

    regex = re.compile("^dbname=.*")
    pos = metadata.index([m.group(0) for l in metadata for m in [regex.search(l)] if m][0])
    tmp = metadata[pos]
    pos = tmp.find("=")
    dbname = tmp[pos + 2:-1]

    regex = re.compile("^user=.*")
    pos = metadata.index([m.group(0) for l in metadata for m in [regex.search(l)] if m][0])
    tmp = metadata[pos]
    pos = tmp.find("=")
    userName = tmp[pos + 2:-1]

    regex = re.compile("^password=.*")
    pos = metadata.index([m.group(0) for l in metadata for m in [regex.search(l)] if m][0])
    tmp = metadata[pos]
    pos = tmp.find("=")
    password = tmp[pos + 2:-1]

    regex = re.compile("^key=.*")
    pos = metadata.index([m.group(0) for l in metadata for m in [regex.search(l)] if m][0])
    tmp = metadata[pos]
    pos = tmp.find("=")
    key = tmp[pos + 2:-1]

    regex = re.compile("^srid=.*")
    pos = metadata.index([m.group(0) for l in metadata for m in [regex.search(l)] if m][0])
    tmp = metadata[pos]
    pos = tmp.find("=")
    srid = tmp[pos + 1:]

    regex = re.compile("^table=.*")
    pos = metadata.index([m.group(0) for l in metadata for m in [regex.search(l)] if m][0])
    tmp = metadata[pos]
    pos = tmp.find("=")
    tmp = tmp[pos + 2:-1].split('"."')
    schema = tmp[0]
    table = tmp[1]

    regex = re.compile("^\(.*\)")
    pos = metadata.index([m.group(0) for l in metadata for m in [regex.search(l)] if m][0])
    column = metadata[pos][1:-1]

    connName = host + ' - ' + dbname + ' - ' + datetime.now().isoformat()
    params = dict(resource=dict(cls='postgis_connection', display_name=connName),
                  postgis_connection=dict(hostname=host, database=dbname,
                  username=userName, password=password))
    url = url + '/resource/' + str(group) + '/child/'
    try:
        pgConn = requests.post(url, auth=auth, data=json.dumps(params))
        if pgConn.status_code != 201:
            raise NGWError(
                'Cannot create resource. Server responce:\n\n%s' % pgConn.content,
                 pgConn.status_code)
    except requests.exceptions.RequestException, e:
        raise NGWError(e.message)

    crs = dict(id=3857)
    params = dict(resource=dict(cls='postgis_layer', display_name=name),
                  postgis_layer=dict(srs=crs, fields='update', connection=pgConn.json(),
                  table=table, schema=schema, column_id=key, column_geom=column))
    try:
        res = requests.post(url, auth=auth, data=json.dumps(params))
        if res.status_code != 201:
            raise NGWError(
                'Cannot create resource. Server responce:\n\n%s' % res.content,
                 res.status_code)
    except requests.exceptions.RequestException, e:
        raise NGWError(e.message)
