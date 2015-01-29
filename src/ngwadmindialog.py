# -*- coding: utf-8 -*-

"""
***************************************************************************
    ngwadmindialog.py
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
from os import path

from PyQt4 import uic


__author__ = 'NextGIS'
__date__ = 'March 2014'
__copyright__ = '(C) 2014, NextGIS'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from PyQt4.QtGui import *

import newconnectiondialog

FORM_CLASS, _ = uic.loadUiType(path.join(
    path.dirname(__file__), 'ui/', 'ngwadmindialogbase.ui'))

from utils import *

class NgwAdminDialog(QDialog, FORM_CLASS):
    def __init__(self, iface):
        QDialog.__init__(self)
        self.setupUi(self)

        self.iface = iface

        self.btnNew.clicked.connect(self.newConnection)
        self.btnEdit.clicked.connect(self.editConnection)
        self.btnDelete.clicked.connect(self.deleteConnection)
        self.btnNewGroup.clicked.connect(self.createGroup)
        self.btnUpload.clicked.connect(self.uploadLayer)
        self.cmbConnections.currentIndexChanged.connect(self.populateResourceGroups)
        self.cmbLayers.currentIndexChanged.connect(self.layerChanged)

        self.manageGui()

    def manageGui(self):
        self.populateConnections()

        settings = QSettings("NextGIS", "ngwadmin")
        lastConnection = settings.value('/ui/lastConnection', '')
        self.cmbConnections.setCurrentIndex(self.cmbConnections.findText(lastConnection))

        layers = getMapLayers()
        for k, v in layers.iteritems():
            self.cmbLayers.addItem(v, k)

    def reject(self):
        settings = QSettings("NextGIS", "ngwadmin")
        settings.setValue('/ui/lastConnection', self.cmbConnections.currentText())
        QDialog.reject(self)

    def newConnection(self):
        dlg = newconnectiondialog.NewConnectionDialog(self)
        if dlg.exec_():
            self.populateConnections()
        del dlg

    def editConnection(self):
        dlg = newconnectiondialog.NewConnectionDialog(self, self.cmbConnections.currentText())
        if dlg.exec_():
            self.populateConnections()
        del dlg

    def deleteConnection(self):
        settings = QSettings("NextGIS", "ngwadmin")
        key = '/connections/' + self.cmbConnections.currentText()
        settings.remove(key + '/url')
        settings.remove(key + '/user')
        settings.remove(key + '/password')
        settings.remove(key)
        self.populateConnections()

    def populateConnections(self):
        self.cmbConnections.blockSignals(True)
        self.cmbConnections.clear()
        settings = QSettings("NextGIS", "ngwadmin")
        settings.beginGroup('/connections')
        self.cmbConnections.addItems(settings.childGroups())
        self.cmbConnections.blockSignals(False)
        settings.endGroup()

        lastConnection = settings.value('/ui/lastConnection', '')
        idx = self.cmbConnections.findText(lastConnection)
        if idx == -1 and self.cmbConnections.count() > 0:
            self.cmbConnections.setCurrentIndex(0)
        else:
            self.cmbConnections.setCurrentIndex(idx)

        self.populateResourceGroups()

        self.btnEdit.setDisabled(self.cmbConnections.count() == 0)
        self.btnDelete.setDisabled(self.cmbConnections.count() == 0)
        self.cmbConnections.setDisabled(self.cmbConnections.count() == 0)
        self.btnNewGroup.setDisabled(self.cmbConnections.count() == 0)
        self.btnUpload.setDisabled(self.cmbConnections.count() == 0)

    def layerChanged(self):
        layerId = self.cmbLayers.itemData(self.cmbLayers.currentIndex())
        layer = getLayerById(layerId)

        self.leDisplayName.setText(layer.name())

    def populateResourceGroups(self):
        self.cmbResources.clear()

        if self.cmbConnections.currentIndex() == -1:
            return

        settings = QSettings("NextGIS", "ngwadmin")
        key = '/connections/' + self.cmbConnections.currentText()
        url = settings.value(key + '/url', '')
        auth = (settings.value(key + '/user', ''), settings.value(key + '/password', ''))

        groups = getResourceGroups(url, auth)
        if groups is not None:
            for k, v in groups.iteritems():
                self.cmbResources.addItem(v, k)

    def createGroup(self):
        groupName = QInputDialog.getText(self, self.tr('Enter group name'), self.tr('Group name'))[0]
        if groupName == '':
            return

        settings = QSettings("NextGIS", "ngwadmin")
        key = '/connections/' + self.cmbConnections.currentText()
        url = settings.value(key + '/url', '')

        auth = (settings.value(key + '/user', ''), settings.value(key + '/password', ''))
        parent = self.cmbResources.itemData(self.cmbResources.currentIndex())

        try:
            addResourceGroup(url, auth, parent, groupName)
        except NGWError, e:
            QMessageBox.critical(self, self.tr('Group creation error'), e.message)

        self.populateResourceGroups()

    def uploadLayer(self):
        settings = QSettings("NextGIS", "ngwadmin")
        key = '/connections/' + self.cmbConnections.currentText()
        url = settings.value(key + '/url', '')
        auth = (settings.value(key + '/user', ''), settings.value(key + '/password', ''))
        group = self.cmbResources.itemData(self.cmbResources.currentIndex())
        dn = self.leDisplayName.text()
        if dn == '':
            QMessageBox.warning(self, self.tr('Wrong name'), self.tr('Display name can not be empty.'))
            return
        self.btnUpload.setEnabled(False)

        layerId = self.cmbLayers.itemData(self.cmbLayers.currentIndex())
        layer = getLayerById(layerId)
        try:
            if layer.providerType() == 'postgres':
                uploadPostgisLayer(url, auth, group, layer, dn)
            elif layer.storageType() == 'ESRI Shapefile':
                uploadShapeLayer(url, auth, group, layer, dn)
        except NGWError, e:
            QMessageBox.critical(self, self.tr('Upload error'), e.message)
        finally:
            self.btnUpload.setEnabled(True)
