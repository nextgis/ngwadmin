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
        self.cmbResources.currentIndexChanged.connect(self.resourceChanged)
        self.cmbLayers.currentIndexChanged.connect(self.layerChanged)

        self.btnNewGroup.setDisabled(True)
        self.btnUpload.setDisabled(True)
        
        self.manageGui()

    def manageGui(self):
        
        self.populateConnections()
        
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
        self.btnNew.setDisabled(True)
        self.btnEdit.setDisabled(True)
        self.btnDelete.setDisabled(True)
          
        settings = QSettings("NextGIS", "ngwadmin")
        key = '/connections/' + self.cmbConnections.currentText()
        settings.remove(key + '/url')
        settings.remove(key + '/user')
        settings.remove(key + '/password')
        settings.remove(key)
        self.populateConnections()
        
        self.btnNew.setDisabled(False)
        self.btnEdit.setDisabled(False)
        self.btnDelete.setDisabled(False)
    
    def populateConnections(self):
        self.cmbResources.clear()
        
        self.cmbConnections.blockSignals(True)
        self.cmbConnections.clear()
        settings = QSettings("NextGIS", "ngwadmin")
        settings.beginGroup('/connections')
        self.cmbConnections.addItems(settings.childGroups())
        self.cmbConnections.setCurrentIndex(-1)
        self.cmbConnections.blockSignals(False)
        settings.endGroup()

        lastConnection = settings.value('/ui/lastConnection', '')
        lastConnectionIndex = self.cmbConnections.findText(lastConnection)
        
        newConnectionName = settings.value('/ui/newConnection', '')
        newConnectionIndex = self.cmbConnections.findText(newConnectionName)
        settings.remove('/ui/newConnection')
        
        
        if newConnectionIndex != -1:
          self.cmbConnections.setCurrentIndex(newConnectionIndex)
        elif lastConnectionIndex == -1 and self.cmbConnections.count() > 0:
          self.cmbConnections.setCurrentIndex(0)
        else:
          self.cmbConnections.setCurrentIndex(lastConnectionIndex)
        
        self.btnEdit.setDisabled(self.cmbConnections.count() == 0)
        self.btnDelete.setDisabled(self.cmbConnections.count() == 0)
        self.cmbConnections.setDisabled(self.cmbConnections.count() == 0)

    def connectionChanged(self):
        self.cmbResources.clear()
        self.__loadResourceGroups()
    
    def __loadResourceGroups(self):
        settings = QSettings("NextGIS", "ngwadmin")
        
        key = '/connections/' + self.cmbConnections.currentText()
        url = settings.value(key + '/url', '')
        auth = (settings.value(key + '/user', ''), settings.value(key + '/password', ''))
        
        try:
          groups = utils.getResourceGroups(url, auth)
          for k, v in groups.iteritems():
              self.cmbResources.addItem(v, k)
        except utils.NGWException as ngwEx:
          QMessageBox.warning(self, self.tr('NGW connection exception'), self.tr('Get resource groups error!\nMessage:\n\t') + ngwEx.message)

    def resourceChanged(self):
        if self.cmbResources.currentIndex() == -1:
          self.btnNewGroup.setDisabled(True)
        else:
          self.btnNewGroup.setDisabled(False)
        
        if self.cmbResources.currentIndex() == -1 or self.cmbLayers.currentIndex() == -1:
          self.btnUpload.setDisabled(True)
        else:
          self.btnUpload.setDisabled(False)
    
    def layerChanged(self):
        if self.cmbResources.currentIndex() == -1 or self.cmbLayers.currentIndex() == -1:
          self.btnUpload.setDisabled(True)
        else:
          self.btnUpload.setDisabled(False)
          
        layerId = self.cmbLayers.itemData(self.cmbLayers.currentIndex())
        layer = utils.getLayerById(layerId)

        self.leDisplayName.setText(layer.name())
    
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
        self.btnUpload.setDisabled(True)
        
        settings = QSettings("NextGIS", "ngwadmin")
        key = '/connections/' + self.cmbConnections.currentText()
        url = settings.value(key + '/url', '')
        auth = (settings.value(key + '/user', ''), settings.value(key + '/password', ''))
        group = self.cmbResources.itemData(self.cmbResources.currentIndex())
        dn = self.leDisplayName.text()
        if dn == '':
            QMessageBox.warning(self, self.tr('Wrong name'), self.tr('Display name can not be empty.'))
            return

        layerId = self.cmbLayers.itemData(self.cmbLayers.currentIndex())
        layer = utils.getLayerById(layerId)
        try:
            if layer.providerType() == 'postgres':
                utils.uploadPostgisLayer(url, auth, group, layer, dn)
            elif layer.storageType() == 'ESRI Shapefile':
                utils.uploadShapeLayer(url, auth, group, layer, dn)
        except:
            pass
        finally:
            self.btnUpload.setDisabled(False)
