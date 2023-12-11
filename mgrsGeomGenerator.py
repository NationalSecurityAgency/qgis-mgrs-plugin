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

from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.uic import loadUiType
from qgis.core import Qgis, QgsFeature, QgsGeometry, QgsProject, QgsPointXY, QgsVectorLayer, QgsField

from . import mgrs
from .settings import epsg4326
import traceback

FORM_CLASS, _ = loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/mgrsGeomGen.ui'))

class MgrsGeomGenerator(QDialog, FORM_CLASS):
    def __init__(self, iface, parent):
        super(MgrsGeomGenerator, self).__init__(parent)
        self.setupUi(self)
        self.iface = iface
        self.canvas = iface.mapCanvas()
        # self.buttonBox.button(QDialogButtonBox.Reset).setText("Clear")

    def accept(self):
        mode = self.modeComboBox.currentIndex()
        pts = []
        mgs = []
        try:
            valuestr = str(self.valuesTextEdit.toPlainText()).strip()
            values = re.split(r'[\s,;:]+', valuestr)
            if len(values) == 0:
                self.iface.messageBar().pushMessage("", "Enter MGRS coordinates", level=Qgis.Warning, duration=4)
                return
            for mg in values:
                lat, lon = mgrs.toWgs(mg)
                pt = QgsPointXY(lon, lat)
                pts.append(pt)
                mgs.append(mg)
        except Exception:
            self.iface.messageBar().pushMessage("", "One or more entered mgrs coordinates were invalid", level=Qgis.Warning, duration=4)
            s = traceback.format_exc()
            print(s)
            return
        
        if mode == 0:  # Points
            layer = QgsVectorLayer("Point?crs={}".format(epsg4326.authid()), "MGRS Points", "memory")
            dp = layer.dataProvider()
            attr = [QgsField('mgrs', QVariant.String),
                QgsField('longitude', QVariant.Double),
                QgsField('latitude', QVariant.Double)]
            dp.addAttributes(attr)
            layer.updateFields()
            for i, pt in enumerate(pts):
                f = QgsFeature()
                f.setGeometry(QgsGeometry.fromPointXY(pt))
                f.setAttributes([mgs[i], pt.x(), pt.y()])
                dp.addFeatures([f])
        elif mode == 1:  # Line
            if len(pts) < 2:
                self.iface.messageBar().pushMessage("", "There must be 2 or more coodinates for a line", level=Qgis.Warning, duration=4)
                return
            layer = QgsVectorLayer("LineString?crs={}".format(epsg4326.authid()), "MGRS Line", "memory")
            dp = layer.dataProvider()
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromPolylineXY(pts))
            dp.addFeatures([f])
        elif mode == 2:  # Polygon
            if len(pts) < 3:
                self.iface.messageBar().pushMessage("", "There must be 3 or more coodinates for a polygon", level=Qgis.Warning, duration=4)
                return
            layer = QgsVectorLayer("Polygon?crs={}".format(epsg4326.authid()), "MGRS Polygon", "memory")
            dp = layer.dataProvider()
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromPolygonXY([pts]))
            dp.addFeatures([f])
        else:  # Minimum bounding box
            if len(pts) < 2:
                self.iface.messageBar().pushMessage("", "There must be 2 or more coodinates for a minimum bounding box", level=Qgis.Warning, duration=4)
                return
            layer = QgsVectorLayer("Polygon?crs={}".format(epsg4326.authid()), "MGRS Bounding Box", "memory")
            dp = layer.dataProvider()
            attr = [QgsField('min_lon', QVariant.Double),
                QgsField('min_lat', QVariant.Double),
                QgsField('max_lon', QVariant.Double),
                QgsField('max_lat', QVariant.Double)]
            dp.addAttributes(attr)
            layer.updateFields()
            minx = miny = 9999
            maxx = maxy = -9999
            for pt in pts:
                x = pt.x()
                y = pt.y()
                if x < minx:
                    minx = x
                if x > maxx:
                    maxx = x
                if y < miny:
                    miny = y
                if y > maxy:
                    maxy = y
            bbox = [
                QgsPointXY(minx, miny),
                QgsPointXY(minx, maxy),
                QgsPointXY(maxx, maxy),
                QgsPointXY(maxx, miny),
                QgsPointXY(minx, miny)
            ]
            f = QgsFeature()
            f.setAttributes([minx, miny, maxx, maxy])
            f.setGeometry(QgsGeometry.fromPolygonXY([bbox]))
            dp.addFeatures([f])


        QgsProject.instance().addMapLayer(layer)
