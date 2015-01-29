# -*- coding: utf-8 -*-

"""
***************************************************************************
    aboutdialog.py
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

__author__ = 'NextGIS'
__date__ = 'March 2014'
__copyright__ = '(C) 2014, NextGIS'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import ConfigParser
from os import path

from PyQt4.QtCore import *
from PyQt4.QtGui import *

FORM_CLASS, _ = uic.loadUiType(path.join(
    path.dirname(__file__), 'ui/', 'aboutdialogbase.ui'))

icon_path = path.join(path.dirname(__file__), 'icons')

class AboutDialog(QDialog, FORM_CLASS):
    def __init__(self):
        QDialog.__init__(self)
        self.setupUi(self)

        self.btnHelp = self.buttonBox.button(QDialogButtonBox.Help)

        self.lblLogo.setPixmap(QPixmap(path.join(icon_path, "ngwadmin.png")))

        cfg = ConfigParser.SafeConfigParser()
        cfg.read(os.path.join(path.dirname(__file__), "metadata.txt"))
        version = cfg.get("general", "version")

        self.lblVersion.setText(self.tr("Version: %s") % (version))
        doc = QTextDocument()
        doc.setHtml(self.getAboutText())
        self.textBrowser.setDocument(doc)
        self.textBrowser.setOpenExternalLinks(True)

        self.buttonBox.helpRequested.connect(self.openHelp)

    def reject(self):
        QDialog.reject(self)

    def openHelp(self):
        overrideLocale = QSettings().value("locale/overrideFlag", False, type=bool)
        if not overrideLocale:
            localeFullName = QLocale.system().name()
        else:
            localeFullName = QSettings().value("locale/userLocale", "")

        localeShortName = localeFullName[0:2]
        if localeShortName in ["ru", "uk"]:
            QDesktopServices.openUrl(QUrl("http://gis-lab.info"))
        else:
            QDesktopServices.openUrl(QUrl("http://gis-lab.info"))

    def getAboutText(self):
        return self.tr("""<p>NextGIS Web administration and management within QGIS</p>
    <p><strong>Developers</strong>: <a href="http://nextgis.org">NextGIS</a>.</p>
    <p><strong>Homepage</strong>: <a href="http://gis-lab.info">http://gis-lab.info</a></p>
    <p>Please report bugs at <a href="http://github.com/nextgis/ngwadmin/issues">bugtracker</a></p>
    """)
