# -*- coding: utf-8 -*-

"""
***************************************************************************
    ngwadmin.py
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

__author__ = 'NextGIS'
__date__ = 'March 2014'
__copyright__ = '(C) 2014, NextGIS'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *

import ngwadmindialog
import aboutdialog

icon_path = path.join(path.dirname(__file__), 'icons')

class NgwAdmin:
    def __init__(self, iface):
        self.iface = iface

        self.qgsVersion = unicode(QGis.QGIS_VERSION_INT)

        userPluginPath = QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "/python/plugins/ngwadmin"
        systemPluginPath = QgsApplication.prefixPath() + "/python/plugins/ngw_admin"

        overrideLocale = QSettings().value("locale/overrideFlag", False, type=bool)
        if not overrideLocale:
            localeFullName = QLocale.system().name()
        else:
            localeFullName = QSettings().value("locale/userLocale", "")

        if QFileInfo(userPluginPath).exists():
            translationPath = userPluginPath + "/i18n/ngwadmin_" + localeFullName + ".qm"
        else:
            translationPath = systemPluginPath + "/i18n/ngwadmin_" + localeFullName + ".qm"

        self.localePath = translationPath
        if QFileInfo(self.localePath).exists():
            self.translator = QTranslator()
            self.translator.load(self.localePath)
            QCoreApplication.installTranslator(self.translator)

    def initGui(self):
        if int(self.qgsVersion) < 20000:
            qgisVersion = self.qgsVersion[0] + "." + self.qgsVersion[2] + "." + self.qgsVersion[3]
            QMessageBox.warning(self.iface.mainWindow(),
                                QCoreApplication.translate("NgwAdmin", "Error"),
                                QCoreApplication.translate("NgwAdmin", "QGIS %s detected.\n") % (qgisVersion) +
                                QCoreApplication.translate("NgwAdmin", "This version of NgwAdmin requires at least QGIS version 2.0. Plugin will not be enabled.")
                               )
            return None

        self.actionRun = QAction(QCoreApplication.translate("NgwAdmin", "NGW Admin"), self.iface.mainWindow())
        self.actionRun.setIcon(QIcon(path.join(icon_path, "ngwadmin.png")))
        self.actionAbout = QAction(QCoreApplication.translate("NgwAdmin", "About..."), self.iface.mainWindow())
        self.actionAbout.setIcon(QIcon(path.join(icon_path, "about.png")))

        self.iface.addPluginToWebMenu(QCoreApplication.translate('NgwAdmin', 'NGW Admin'), self.actionRun)
        self.iface.addPluginToWebMenu(QCoreApplication.translate('NgwAdmin', 'NGW Admin'), self.actionAbout)
        self.iface.addWebToolBarIcon(self.actionRun)

        self.actionRun.triggered.connect(self.run)
        self.actionAbout.triggered.connect(self.about)

    def unload(self):
        self.iface.removePluginWebMenu(QCoreApplication.translate('NgwAdmin', 'NGW Admin'), self.actionRun)
        self.iface.removePluginWebMenu(QCoreApplication.translate('NgwAdmin', 'NGW Admin'), self.actionAbout)
        self.iface.removeWebToolBarIcon(self.actionRun)

    def run(self):
        d = ngwadmindialog.NgwAdminDialog(self.iface)
        d.show()
        d.exec_()

    def about(self):
        dlg = aboutdialog.AboutDialog()
        dlg.exec_()
