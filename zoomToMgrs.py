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
import os
import re

from qgis.PyQt.uic import loadUiType
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QDockWidget
from qgis.PyQt.QtCore import QTimer, Qt
from qgis.gui import QgsVertexMarker, QgsRubberBand
from qgis.core import Qgis, QgsWkbTypes, QgsPoint, QgsGeometry, QgsCoordinateTransform, QgsProject, QgsRectangle, QgsPointXY
# import traceback

from .settings import settings, epsg4326
from . import mgrs

FORM_CLASS, _ = loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/zoomToMgrs.ui'))


class ZoomToMgrs(QDockWidget, FORM_CLASS):

    def __init__(self, iface, parent):
        super(ZoomToMgrs, self).__init__(parent)
        self.setupUi(self)
        self.canvas = iface.mapCanvas()
        self.crossRb = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self.crossRb.setColor(Qt.red)
        self.marker = None
        self.zoomToolButton.setIcon(QIcon(':/images/themes/default/mActionZoomIn.svg'))
        self.clearToolButton.setIcon(QIcon(':/images/themes/default/mIconClearText.svg'))
        self.zoomToolButton.clicked.connect(self.zoomToPressed)
        self.clearToolButton.clicked.connect(self.removeMarker)
        self.iface = iface
        self.coordTxt.returnPressed.connect(self.zoomToPressed)

    def closeEvent(self, event):
        self.removeMarker()
        event.accept()
        
    def zoomToPressed(self):
        try:
            text = self.coordTxt.text().strip()
            text2 = re.sub(r'\s+', '', str(text))
            lat, lon = mgrs.toWgs(text2)
            pt = self.zoomTo(epsg4326, lat, lon)
            if settings.persistentMarker:
                if self.marker is None:
                    self.marker = QgsVertexMarker(self.canvas)
                self.marker.setCenter(pt)
                self.marker.setIconSize(18)
                self.marker.setPenWidth(2)
                self.marker.setIconType(QgsVertexMarker.ICON_CROSS)
            elif self.marker is not None:
                self.removeMarker()
        except Exception:
            # traceback.print_exc()
            self.iface.messageBar().pushMessage("", "Invalid MGRS Coordinate", level=Qgis.Warning, duration=2)
            return

    def removeMarker(self):
        if self.marker is not None:
            self.canvas.scene().removeItem(self.marker)
            self.marker = None
        self.coordTxt.clear()

    def zoomTo(self, srcCrs, lat, lon):
        canvasCrs = self.canvas.mapSettings().destinationCrs()
        transform = QgsCoordinateTransform(srcCrs, canvasCrs, QgsProject.instance())
        x, y = transform.transform(float(lon), float(lat))

        rect = QgsRectangle(x, y, x, y)
        self.canvas.setExtent(rect)

        pt = QgsPointXY(x, y)
        self.highlight(pt)
        self.canvas.refresh()
        return pt

    def highlight(self, point):
        currExt = self.canvas.extent()

        leftPt = QgsPoint(currExt.xMinimum(), point.y())
        rightPt = QgsPoint(currExt.xMaximum(), point.y())

        topPt = QgsPoint(point.x(), currExt.yMaximum())
        bottomPt = QgsPoint(point.x(), currExt.yMinimum())

        horizLine = QgsGeometry.fromPolyline([leftPt, rightPt])
        vertLine = QgsGeometry.fromPolyline([topPt, bottomPt])

        self.crossRb.reset(QgsWkbTypes.LineGeometry)
        self.crossRb.addGeometry(horizLine, None)
        self.crossRb.addGeometry(vertLine, None)

        QTimer.singleShot(700, self.resetRubberbands)

    def resetRubberbands(self):
        self.crossRb.reset()
