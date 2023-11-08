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

from qgis.PyQt.QtCore import Qt, QVariant, QUrl
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsFields, QgsField, QgsFeature, QgsWkbTypes, QgsRectangle, QgsGeometry, QgsVectorLayer, QgsPalLayerSettings, QgsVectorLayerSimpleLabeling
from qgis.utils import iface

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterBoolean,
    QgsProcessingLayerPostProcessorInterface,
    QgsProcessingParameterFeatureSink)

from .settings import settings, epsg4326

bands = ['C','D','E','F','G','H','J','K','L','M','N','P','Q','R','S','T','U','V','W','X']

class MgrsGzdAlgorithm(QgsProcessingAlgorithm):
    """
    Algorithm to convert a point layer to a MGRS field.
    """
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.
    PrmPolarRegions = 'Polar'
    PrmOutput = 'Output'
    PrmStyle = 'Style'

    def initAlgorithm(self, config):
        self.addParameter(
            QgsProcessingParameterBoolean (
                self.PrmPolarRegions,
                'Include polar regions',
                True,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterBoolean (
                self.PrmStyle,
                'Automatically style output',
                True,
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.PrmOutput,
                'MGRS Grid Zone Designator')
        )

    def processAlgorithm(self, parameters, context, feedback):
        polar = self.parameterAsBoolean(parameters, self.PrmPolarRegions, context)
        auto_style = self.parameterAsBoolean(parameters, self.PrmStyle, context)

        f = QgsFields()
        f.append(QgsField("GZD", QVariant.String))

        (sink, dest_id) = self.parameterAsSink(
            parameters, self.PrmOutput,
            context, f, QgsWkbTypes.Polygon, epsg4326)
        if polar:
            self.exportPolygon(sink, -180, -90, 180, 10, 'A')
            self.exportPolygon(sink, 0, -90, 180, 10, 'B')
        lat = -80
        for b in bands:
            if b == 'X':
                height = 12
                lon = -180
                for i in range(1, 31):
                    gzd = '{:02d}{}'.format(i, b)
                    width = 6
                    self.exportPolygon(sink, lon, lat, width, height, gzd)
                    lon += width
                self.exportPolygon(sink, lon, lat, 9, height, '31X')
                lon += 9
                self.exportPolygon(sink, lon, lat, 12, height, '33X')
                lon += 12
                self.exportPolygon(sink, lon, lat, 12, height, '35X')
                lon += 12
                self.exportPolygon(sink, lon, lat, 9, height, '37X')
                lon += 9
                for i in range(38, 61):
                    gzd = '{:02d}{}'.format(i, b)
                    width = 6
                    self.exportPolygon(sink, lon, lat, width, height, gzd)
                    lon += width
            else:
                height = 8
                lon = -180
                for i in range(1, 61):
                    gzd = '{:02d}{}'.format(i, b)
                    if b == 'V' and i == 31:
                        width = 3
                    elif b == 'V' and i == 32:
                        width = 9
                    else:
                        width = 6
                    self.exportPolygon(sink, lon, lat, width, height, gzd)
                    lon += width
            lat += height

        if polar:
            self.exportPolygon(sink, -180, 84, 180, 6, 'Y')
            self.exportPolygon(sink, 0, 84, 180, 6, 'Z')

        if auto_style:
            if context.willLoadLayerOnCompletion(dest_id):
                context.layerToLoadOnCompletionDetails(dest_id).setPostProcessor(StylePostProcessor.create(settings.lineColor, settings.fontColor))
        return {self.PrmOutput: dest_id}

    def exportPolygon(self, sink, lon, lat, width, height, gzd):
        rect = QgsRectangle(lon, lat, lon+width, lat+height)
        f = QgsFeature()
        f.setGeometry(QgsGeometry.fromRect(rect))
        f.setAttributes([gzd])
        sink.addFeature(f)

    def name(self):
        return 'mgrsgzd'

    def displayName(self):
        return 'MGRS Grid Zone Designator'

    def helpUrl(self):
        file = os.path.dirname(__file__) + '/index.html'
        if not os.path.exists(file):
            return ''
        return QUrl.fromLocalFile(file).toString(QUrl.FullyEncoded)

    def createInstance(self):
        return MgrsGzdAlgorithm()


class StylePostProcessor(QgsProcessingLayerPostProcessorInterface):
    instance = None
    line_color = None
    font_color = None

    def __init__(self, line_color, font_color):
        self.line_color = line_color
        self.font_color = font_color
        super().__init__()

    def postProcessLayer(self, layer, context, feedback):

        if not isinstance(layer, QgsVectorLayer):
            return
        sym = layer.renderer().symbol().symbolLayer(0)
        sym.setBrushStyle(Qt.NoBrush)
        sym.setStrokeColor(self.line_color)
        label = QgsPalLayerSettings()
        label.fieldName = 'GZD'
        format = label.format()
        format.setColor(self.font_color)
        format.setSize(8)
        label.setFormat(format)
        labeling = QgsVectorLayerSimpleLabeling(label)
        layer.setLabeling(labeling)
        layer.setLabelsEnabled(True)
        iface.layerTreeView().refreshLayerSymbology(layer.id())

    # Hack to work around sip bug!
    @staticmethod
    def create(line_color, font_color) -> 'StylePostProcessor':
        """
        Returns a new instance of the post processor, keeping a reference to the sip
        wrapper so that sip doesn't get confused with the Python subclass and call
        the base wrapper implementation instead... ahhh sip, you wonderful piece of sip
        """
        StylePostProcessor.instance = StylePostProcessor(line_color, font_color)
        return StylePostProcessor.instance
