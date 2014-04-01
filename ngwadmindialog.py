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

__author__ = 'NextGIS'
__date__ = 'March 2014'
__copyright__ = '(C) 2014, NextGIS'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import locale
import operator

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *

import newconnectiondialog

from ui.ui_ngwadmindialogbase import Ui_Dialog

import utils


class NgwAdminDialog(QDialog, Ui_Dialog):
    def __init__(self, iface):
        QDialog.__init__(self)
        self.setupUi(self)

        self.iface = iface

        self.btnNew.clicked.connect(self.newConnection)
        self.btnEdit.clicked.connect(self.editConnection)
        self.btnDelete.clicked.connect(self.deleteConnection)
        self.btnNewGroup.clicked.connect(self.createGroup)
        self.btnUpload.clicked.connect(self.uploadLayer)
        self.cmbConnections.currentIndexChanged.connect(self.connectionChanged)
        self.cmbLayers.currentIndexChanged.connect(self.layerChanged)

        self.manageGui()

    def manageGui(self):
        self.populateConnections()
        settings = QSettings("NextGIS", "ngwadmin")
        lastConnection = settings.value('/ui/lastConnection', '')
        self.cmbConnections.setCurrentIndex(self.cmbConnections.findText(lastConnection))

        if self.cmbConnections.currentIndex() != -1:
            key = '/connections/' + self.cmbConnections.currentText()
            url = settings.value(key + '/url', '')
            auth = (settings.value(key + '/user', ''), settings.value(key + '/password', ''))
            groups = utils.getResourceGroups(url, auth)
            if groups is not None:
                for k, v in groups.iteritems():
                    self.cmbResources.addItem(v, k)

        layers = utils.getMapLayers()
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

        self.populateConnectionList()

    def populateConnections(self):
        self.cmbConnections.blockSignals(True)
        self.cmbConnections.clear()
        settings = QSettings("NextGIS", "ngwadmin")
        settings.beginGroup('/connections')
        self.cmbConnections.addItems(settings.childGroups())
        self.cmbConnections.blockSignals(False)
        settings.endGroup()

        lastConnection = settings.value('/ui/lastConnection', '')
        self.cmbConnections.setCurrentIndex(self.cmbConnections.findText(lastConnection))
        if self.cmbConnections.currentIndex() == -1 and self.cmbConnections.count() > 0:
            self.cmbConnections.setCurrentIndex(0)

        self.btnEdit.setDisabled(self.cmbConnections.count() == 0)
        self.btnDelete.setDisabled(self.cmbConnections.count() == 0)
        self.cmbConnections.setDisabled(self.cmbConnections.count() == 0)

    def layerChanged(self):
        layerId = self.cmbLayers.itemData(self.cmbLayers.currentIndex())
        layer = utils.getLayerById(layerId)

        self.leDisplayName.setText(layer.name())

    def connectionChanged(self):
        self.cmbResources.clear()
        settings = QSettings("NextGIS", "ngwadmin")
        key = '/connections/' + self.cmbConnections.currentText()
        url = settings.value(key + '/url', '')
        auth = (settings.value(key + '/user', ''), settings.value(key + '/password', ''))
        groups = utils.getResourceGroups(url, auth)
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

        utils.addResourceGroup(url, auth, parent, groupName)
        self.connectionChanged()

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
        layer = utils.getLayerById(layerId)
        try:
            if layer.providerType() == 'postgres':
                utils.uploadPostgisLayer(url, auth, group, layer, dn)
            elif layer.storageType() == 'ESRI Shapefile':
                utils.uploadShapeLayer(url, auth, group, layer, dn)
        except:
            self.btnUpload.setEnabled(True)
