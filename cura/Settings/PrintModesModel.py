from PyQt5.QtCore import pyqtProperty, pyqtSlot, pyqtSignal

import UM.Qt.ListModel
from UM.Application import Application
from cura.Settings.ExtruderManager import ExtruderManager

class PrintModesModel(UM.Qt.ListModel.ListModel):

    def __init__(self, parent = None):
        super().__init__(parent)
        Application.getInstance().globalContainerStackChanged.connect(self._onPrinterChanged)
        self._container = Application.getInstance().getGlobalContainerStack()
        if self._container is not None:
            self._container.propertyChanged.connect(self._onPropertyChanged)
            self._enabled = self._container.getProperty("print_mode", "enabled")
            self._print_modes = self._container.getProperty("print_mode", "options")
        else:
            self._enabled = False

    @pyqtProperty("QStringList", constant=True)
    def printModes(self):
        return list(self._print_modes.values())

    @pyqtProperty(int, constant=True)
    def activeIndex(self): # Peta quan no hi ha printer
        currentkey = self._container.getProperty("print_mode", "value")
        currentValue = self._print_modes.get(currentkey)
        return list(self._print_modes.values()).index(currentValue)

    @pyqtProperty(bool, constant=True)
    def visible(self):
        return self._enabled

    @pyqtSlot(str)
    def changeProperty(self, value):
        if value:
            key = next(x for x in self._print_modes if self._print_modes[x] == value)
            self._container.setProperty("print_mode", "value", key)

    @pyqtSlot()
    def update(self):
        self._container = Application.getInstance().getGlobalContainerStack()
        self._container.propertyChanged.disconnect(self._onPropertyChanged)
        self._container.propertyChanged.connect(self._onPropertyChanged)
        self._enabled = self._container.getProperty("print_mode", "enabled")
        self._print_modes = self._container.getProperty("print_mode", "options")

    printModeChanged = pyqtSignal()

    def _onPropertyChanged(self, key, property_name):
        if key == "print_mode" and property_name == "value":
            self.printModeChanged.emit()
            value = self._container.getProperty(key, property_name)
            if value != "regular":
                ExtruderManager.getInstance().setActiveExtruderIndex(0)

    printerChanged = pyqtSignal()

    def _onPrinterChanged(self):
        self._container = Application.getInstance().getGlobalContainerStack()
        self.printerChanged.emit()