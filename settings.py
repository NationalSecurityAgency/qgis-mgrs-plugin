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
from qgis.PyQt.uic import loadUiType
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox
from qgis.PyQt.QtCore import QSettings, Qt
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsCoordinateReferenceSystem


FORM_CLASS, _ = loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/mgrsSettings.ui'))

epsg4326 = QgsCoordinateReferenceSystem('EPSG:4326')


def formatMgrsString(mgrs, add_spaces=False):
    if add_spaces:
        gzd = mgrs[0:3].strip()
        gsid = mgrs[3:5]
        ns = mgrs[5:].strip()
        if len(mgrs) > 5:
            l = int(len(ns) / 2)
            easting = ns[0:l]
            northing = ns[l:]
            s = '{} {} {} {}'.format(gzd, gsid, easting, northing)
        else:
            s = '{} {}'.format(gzd, gsid)
        return(s)
    else:
        return(mgrs.strip())

class Settings():
    def __init__(self):
        self.readSettings()

    def readSettings(self):
        '''Load the user selected settings. The settings are retained even when
        the user quits QGIS. This just loads the saved information into variables,
        but does not update the widgets. The widgets are updated with showEvent.'''
        qset = QSettings()

        self.mgrsPrecision =  int(qset.value('/MGRS/Precision', 5))
        self.mgrsPrefix = qset.value('/MGRS/Prefix', '')
        self.mgrsSuffix = qset.value('/MGRS/Suffix', '')
        self.showLocation = int(qset.value('/MGRS/ShowLocation', Qt.Unchecked))
        self.persistentMarker = int(qset.value('/MGRS/PersistentMarker', Qt.Checked))
        self.addSpaces = int(qset.value('/MGRS/AddSpaces', Qt.Unchecked))
        self.lineColor = QColor(qset.value('/MGRS/LineColor', '#000000'))
        self.fontColor = QColor(qset.value('/MGRS/FontColor', '#000000'))

settings = Settings()


class SettingsWidget(QDialog, FORM_CLASS):
    '''Settings Dialog box.'''
    def __init__(self, iface):
        super(SettingsWidget, self).__init__(iface.mainWindow())
        self.setupUi(self)

        self.buttonBox.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self.restoreDefaults)

        settings.readSettings()

    def restoreDefaults(self):
        '''Restore all settings to their default state.'''
        self.mgrsPrecisionSpinBox.setValue(5)
        self.prefixLineEdit.setText('')
        self.suffixLineEdit.setText('')
        self.markerCheckBox.setCheckState(Qt.Unchecked)
        self.persistentMarkerCheckBox.setCheckState(Qt.Checked)
        self.addSpacesCheckBox.setCheckState(Qt.Unchecked)
        color = QColor('#000000')
        self.lineColorButton.setColor(color)
        self.fontColorButton.setColor(color)

    def accept(self):
        '''Accept the settings and save them for next time.'''
        qset = QSettings()
        qset.setValue('/MGRS/Precision', self.mgrsPrecisionSpinBox.value())
        qset.setValue('/MGRS/Prefix', self.prefixLineEdit.text())
        qset.setValue('/MGRS/Suffix', self.suffixLineEdit.text())
        qset.setValue('/MGRS/ShowLocation', self.markerCheckBox.checkState())
        qset.setValue('/MGRS/PersistentMarker', self.persistentMarkerCheckBox.checkState())
        qset.setValue('/MGRS/AddSpaces', self.addSpacesCheckBox.checkState())
        color = self.lineColorButton.color()
        qset.setValue('/MGRS/LineColor', color.name())
        color = self.fontColorButton.color()
        qset.setValue('/MGRS/FontColor', color.name())

        # The values have been read from the widgets and saved to the registry.
        # Now we will read them back to the variables.
        settings.readSettings()
        self.close()

    def showEvent(self, e):
        '''The user has selected the settings dialog box so we need to
        read the settings and update the dialog box with the previously
        selected settings.'''
        settings.readSettings()
        self.mgrsPrecisionSpinBox.setValue(settings.mgrsPrecision)
        self.prefixLineEdit.setText(settings.mgrsPrefix)
        self.suffixLineEdit.setText(settings.mgrsSuffix)
        self.markerCheckBox.setCheckState(settings.showLocation)
        self.persistentMarkerCheckBox.setCheckState(settings.persistentMarker)
        self.addSpacesCheckBox.setCheckState(settings.addSpaces)
        self.lineColorButton.setColor(settings.lineColor)
        self.fontColorButton.setColor(settings.fontColor)
