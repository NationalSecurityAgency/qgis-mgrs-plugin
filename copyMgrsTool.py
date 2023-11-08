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
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QApplication
from qgis.core import Qgis, QgsCoordinateTransform, QgsPointXY, QgsProject, QgsSettings
from qgis.gui import QgsMapToolEmitPoint, QgsVertexMarker

from .settings import settings, epsg4326, formatMgrsString
from . import mgrs
# import traceback

class CopyMgrsTool(QgsMapToolEmitPoint):
    '''Class to interact with the map canvas to capture the coordinate
    when the mouse button is pressed and to display the coordinate in
    in the status bar.'''
    captureStopped = pyqtSignal()

    def __init__(self, iface):
        QgsMapToolEmitPoint.__init__(self, iface.mapCanvas())
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.marker = None
        self.vertex = None

    def activate(self):
        '''When activated set the cursor to a crosshair.'''
        self.canvas.setCursor(Qt.CrossCursor)
        self.snapcolor = QgsSettings().value( "/qgis/digitizing/snap_color" , QColor( Qt.magenta ) )

    def deactivate(self):
        self.removeMarker()
        self.removeVertexMarker()
        self.captureStopped.emit()

    def formatCoord(self, pt):
        '''Format the coordinate string according to the settings from
        the settings dialog.'''
        # Make sure the coordinate is transformed to EPSG:4326
        canvasCRS = self.canvas.mapSettings().destinationCrs()
        if canvasCRS == epsg4326:
            pt4326 = pt
        else:
            transform = QgsCoordinateTransform(canvasCRS, epsg4326, QgsProject.instance())
            pt4326 = transform.transform(pt.x(), pt.y())
        try:
            msg = mgrs.toMgrs(pt4326.y(), pt4326.x(), settings.mgrsPrecision)
            msg = formatMgrsString(msg, settings.addSpaces)
        except Exception:
            # traceback.print_exc()
            msg = None

        msg = '{}{}{}'.format(settings.mgrsPrefix, msg, settings.mgrsSuffix)
        return msg

    def canvasMoveEvent(self, event):
        '''Capture the coordinate as the user moves the mouse over
        the canvas. Show it in the status bar.'''
        pt = self.snappoint(event.originalPixelPoint()) # input is QPoint
        try:
            msg = self.formatCoord(pt)
            if msg is None:
                self.iface.statusBarIface().showMessage("")
            else:
                self.iface.statusBarIface().showMessage("{}".format(msg), 4000)
        except Exception:
            self.iface.statusBarIface().showMessage("")

    def snappoint(self, qpoint):
        match = self.canvas.snappingUtils().snapToMap(qpoint)
        if match.isValid():
            if self.vertex is None:
                self.vertex = QgsVertexMarker(self.canvas)
                self.vertex.setIconSize(12)
                self.vertex.setPenWidth(2)
                self.vertex.setColor(self.snapcolor)
                self.vertex.setIconType(QgsVertexMarker.ICON_BOX)
            self.vertex.setCenter(match.point())
            return (match.point()) # Returns QgsPointXY
        else:
            self.removeVertexMarker()
            return self.toMapCoordinates(qpoint) # QPoint input, returns QgsPointXY

    def canvasReleaseEvent(self, event):
        '''Capture the coordinate when the mouse button has been released,
        format it, and copy it to the clipboard. pt is QgsPointXY'''
        pt = self.snappoint(event.originalPixelPoint())
        self.removeVertexMarker()
        if settings.showLocation:
            if self.marker is None:
                self.marker = QgsVertexMarker(self.canvas)
                self.marker.setIconSize(18)
                self.marker.setPenWidth(2)
                self.marker.setIconType(QgsVertexMarker.ICON_CROSS)
            self.marker.setCenter(pt)
        else:
            self.removeMarker()

        try:
            msg = self.formatCoord(pt)
            if msg is not None:
                clipboard = QApplication.clipboard()
                clipboard.setText(msg)
                self.iface.messageBar().pushMessage("", "MGRS coordinate {} copied to the clipboard".format(msg), level=Qgis.Info, duration=4)
        except Exception as e:
            self.iface.messageBar().pushMessage("", "Invalid coordinate: {}".format(e), level=Qgis.Warning, duration=4)

    def removeMarker(self):
        if self.marker is not None:
            self.canvas.scene().removeItem(self.marker)
            self.marker = None

    def removeVertexMarker(self):
        if self.vertex is not None:
            self.canvas.scene().removeItem(self.vertex)
            self.vertex = None
