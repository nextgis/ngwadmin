# -*- coding: utf-8 -*-

"""
***************************************************************************
    newconnectiondialog.py
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
from PyQt4 import uic
from os import path

__author__ = 'NextGIS'
__date__ = 'March 2014'
__copyright__ = '(C) 2014, NextGIS'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from PyQt4.QtCore import *
from PyQt4.QtGui import *

FORM_CLASS, _ = uic.loadUiType(path.join(
    path.dirname(__file__), 'ui/', 'newconnectiondialogbase.ui'))

class NewConnectionDialog(QDialog, FORM_CLASS):
    def __init__(self, parent, connName=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.connName = connName

        if self.connName is not None:
            settings = QSettings('NextGIS', 'ngwadmin')
            key = '/connections/' + self.connName

            self.leName.setText(self.connName)
            self.leUrl.setText(settings.value(key + '/url', ''))
            self.leUser.setText(settings.value(key + '/user', ''))
            self.lePassword.setText(settings.value(key + '/password', ''))

    def accept(self):
        if self.leName.text() == '':
            QMessageBox.warning(self, self.tr('Wrong name'), self.tr('Connection name can not be empty.'))
            return

        if self.leUrl.text() == '':
            QMessageBox.warning(self, self.tr('Wrong URL'), self.tr('URL can not be empty.'))
            return

        settings = QSettings('NextGIS', 'ngwadmin')
        if self.connName is not None and self.connName != self.leName.text():
            settings.remove('/connections/' + self.connName)

        key = '/connections/' + self.leName.text()
        settings.setValue(key + '/url', self.leUrl.text())
        settings.setValue(key + '/user', self.leUser.text())
        settings.setValue(key + '/password', self.lePassword.text())

        QDialog.accept(self)
