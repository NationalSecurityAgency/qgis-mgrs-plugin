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
from geographiclib.geodesic import Geodesic
from geographiclib.polygonarea import PolygonArea

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
        geod = Geodesic.WGS84
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
            # Calculate the line distance in meters
            pt1 = pts[0]
            distance = 0
            for i in range(1, len(pts)):
                pt2 = pts[i]
                l = geod.Inverse(pt1.y(), pt1.x(), pt2.y(), pt2.x())
                distance += l['s12']
            layer = QgsVectorLayer("LineString?crs={}".format(epsg4326.authid()), "MGRS Line", "memory")
            dp = layer.dataProvider()
            attr = [QgsField('distance', QVariant.Double)]
            dp.addAttributes(attr)
            layer.updateFields()
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromPolylineXY(pts))
            f.setAttributes([distance])
            dp.addFeatures([f])
        elif mode == 2:  # Polygon
            if len(pts) < 2:
                self.iface.messageBar().pushMessage("", "There must be 2 or more coodinates for a polygon", level=Qgis.Warning, duration=4)
                return
            # Check to see if the polygon is closed. If it isn't close it.
            if mgs[0] != mgs[len(mgs)-1]:
                mgs.append(mgs[0])
                pts.append(pts[0])
                
            poly = PolygonArea(geod)
            for i in range(len(pts)):
                poly.AddPoint(pts[i].y(), pts[i].x())
            s = poly.Compute()
            layer = QgsVectorLayer("Polygon?crs={}".format(epsg4326.authid()), "MGRS Polygon", "memory")
            dp = layer.dataProvider()
            attr = [QgsField('perimeter', QVariant.Double),
                QgsField('area', QVariant.Double),
                QgsField('valid_geom', QVariant.Bool)]
            dp.addAttributes(attr)
            layer.updateFields()
            f = QgsFeature()
            geom = QgsGeometry.fromPolygonXY([pts])
            valid = geom.isGeosValid()
            f.setGeometry(geom)
            f.setAttributes([s[1],abs(s[2]), valid])
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
                QgsField('max_lat', QVariant.Double),
                QgsField('perimeter', QVariant.Double),
                QgsField('area', QVariant.Double)]
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
            poly = PolygonArea(geod)
            for i in range(len(bbox)):
                poly.AddPoint(bbox[i].y(), bbox[i].x())
            s = poly.Compute(reverse=True)
            f = QgsFeature()
            f.setAttributes([minx, miny, maxx, maxy, s[1], s[2]])
            f.setGeometry(QgsGeometry.fromPolygonXY([bbox]))
            dp.addFeatures([f])


        QgsProject.instance().addMapLayer(layer)
