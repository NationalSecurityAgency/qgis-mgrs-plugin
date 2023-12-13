"""
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import Qt, QUrl
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsApplication
import processing

from .provider import MGRSProvider

from .zoomToMgrs import ZoomToMgrs
from .copyMgrsTool import CopyMgrsTool
from .mgrsGeomGenerator import MgrsGeomGenerator
from .settings import SettingsWidget
import os
import webbrowser


class MGRSCapture:
    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.toolbar = self.iface.addToolBar('MGRS Toolbar')
        self.toolbar.setObjectName('MGRSToolbar')
        self.provider = MGRSProvider()

    def initGui(self):
        '''Initialize Lot Lon Tools GUI.'''
        # Initialize the Settings Dialog box
        self.settingsDialog = SettingsWidget(self.iface)
        self.mapTool = CopyMgrsTool(self.iface)

        # Add Interface for Coordinate Capturing
        icon = QIcon(os.path.dirname(__file__) + "/images/copyMgrs.svg")
        self.copyAction = QAction(icon, "Copy/Display MGRS Coordinate", self.iface.mainWindow())
        self.copyAction.setObjectName('mgrsCopy')
        self.copyAction.triggered.connect(self.startCapture)
        self.copyAction.setCheckable(True)
        self.toolbar.addAction(self.copyAction)
        self.iface.addPluginToMenu("MGRS", self.copyAction)

        # Add Interface for Zoom to Coordinate
        icon = QIcon(os.path.dirname(__file__) + "/images/zoomToMgrs.svg")
        self.zoomToAction = QAction(icon, "Zoom To MGRS Coordinate", self.iface.mainWindow())
        self.zoomToAction.setObjectName('mgrsZoom')
        self.zoomToAction.triggered.connect(self.showZoomToDialog)
        self.toolbar.addAction(self.zoomToAction)
        self.iface.addPluginToMenu('MGRS', self.zoomToAction)

        self.zoomToDialog = ZoomToMgrs(self.iface, self.iface.mainWindow())
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.zoomToDialog)
        self.zoomToDialog.hide()

        # Add Interface for MGRS geometry gnerator
        icon = QIcon(os.path.dirname(__file__) + "/images/mgrsGeom.svg")
        self.geomGenAction = QAction(icon, "MGRS Geometry Generator", self.iface.mainWindow())
        self.geomGenAction.setObjectName('mgrsGeomGenerator')
        self.geomGenAction.triggered.connect(self.showGeometryGenerator)
        self.toolbar.addAction(self.geomGenAction)
        self.iface.addPluginToMenu('MGRS', self.geomGenAction)

        self.geomGenDialog = MgrsGeomGenerator(self.iface, self.iface.mainWindow())
        self.geomGenDialog.hide()
        
        # MGRS Grid Zone Designator
        icon = QIcon(':/images/themes/default/processingAlgorithm.svg')
        self.gzdAction = QAction(icon, "MGRS Grid Zone Designator", self.iface.mainWindow())
        self.gzdAction.triggered.connect(self.gzd)
        self.iface.addPluginToMenu("MGRS", self.gzdAction)

        # Initialize the Settings Dialog Box
        settingsicon = QIcon(':/images/themes/default/mActionOptions.svg')
        self.settingsAction = QAction(settingsicon, "Settings", self.iface.mainWindow())
        self.settingsAction.setObjectName('mgrsSettings')
        self.settingsAction.triggered.connect(self.settings)
        self.iface.addPluginToMenu('MGRS', self.settingsAction)

        # Help
        icon = QIcon(os.path.dirname(__file__) + '/images/help.svg')
        self.helpAction = QAction(icon, "Help", self.iface.mainWindow())
        self.helpAction.setObjectName('mgrsHelp')
        self.helpAction.triggered.connect(self.help)
        self.iface.addPluginToMenu('MGRS', self.helpAction)

        self.canvas.mapToolSet.connect(self.resetTools)

        # Add the processing provider
        QgsApplication.processingRegistry().addProvider(self.provider)

    def resetTools(self, newtool, oldtool):
        '''Uncheck the Copy MGRS tool'''
        try:
            if oldtool is self.mapTool:
                self.copyAction.setChecked(False)
            if newtool is self.mapTool:
                self.copyAction.setChecked(True)
        except Exception:
            pass

    def unload(self):
        '''Unload LatLonTools from the QGIS interface'''
        self.zoomToDialog.removeMarker()
        self.canvas.unsetMapTool(self.mapTool)
        self.iface.removePluginMenu('MGRS', self.copyAction)
        self.iface.removePluginMenu('MGRS', self.zoomToAction)
        self.iface.removePluginMenu('MGRS', self.geomGenAction)
        self.iface.removePluginMenu('MGRS', self.gzdAction)
        self.iface.removePluginMenu('MGRS', self.settingsAction)
        self.iface.removePluginMenu('MGRS', self.helpAction)
        self.iface.removeDockWidget(self.zoomToDialog)
        # Remove Toolbar Icons
        self.iface.removeToolBarIcon(self.copyAction)
        self.iface.removeToolBarIcon(self.zoomToAction)
        self.iface.removeToolBarIcon(self.geomGenAction)
        del self.toolbar

        self.geomGenDialog = None
        self.zoomToDialog = None
        self.settingsDialog = None
        self.mapTool = None
        QgsApplication.processingRegistry().removeProvider(self.provider)

    def startCapture(self):
        '''Set the focus of the copy coordinate tool'''
        self.canvas.setMapTool(self.mapTool)

    def showZoomToDialog(self):
        '''Show the zoom to docked widget.'''
        self.zoomToDialog.show()

    def showGeometryGenerator(self):
        '''Show geometry generator dialog.'''
        self.geomGenDialog.show()

    def gzd(self):
        processing.execAlgorithmDialog('mgrs:mgrsgzd', {})

    def settings(self):
        '''Show the settings dialog box'''
        self.settingsDialog.show()

    def help(self):
        '''Display a help page'''
        url = QUrl.fromLocalFile(os.path.dirname(__file__) + "/index.html").toString()
        webbrowser.open(url, new=2)

