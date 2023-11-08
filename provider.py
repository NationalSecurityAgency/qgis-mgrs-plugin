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
from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon
from .mgrsgzd import MgrsGzdAlgorithm


class MGRSProvider(QgsProcessingProvider):

    def unload(self):
        QgsProcessingProvider.unload(self)

    def loadAlgorithms(self):
        self.addAlgorithm(MgrsGzdAlgorithm())

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/images/copyMgrs.svg')

    def id(self):
        return 'mgrs'

    def name(self):
        return 'MGRS'

    def longName(self):
        return self.name()
