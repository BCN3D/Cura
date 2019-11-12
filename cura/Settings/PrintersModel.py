from PyQt5.QtCore import pyqtSlot

from UM.Settings.Models.DefinitionContainersModel import DefinitionContainersModel

from cura.Bcn3DApi.DataApiService import DataApiService
from cura.Bcn3DApi.AuthApiService import AuthApiService


class PrintersModel(DefinitionContainersModel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data_api_service = DataApiService.getInstance()

    @pyqtSlot()
    def updateNetworkPrinters(self):
        self.clear()
        self._update()
        if AuthApiService.getInstance().isLoggedIn:
            printers = self._data_api_service.getPrinters()
            for printer in printers:
                item = {
                    "name": printer["printerName"],
                    "id": "bcn3depsilon",
                    "section": "Network Printers",
                    "additional_info": "Serial Number: " + printer["serialNumber"],
                    "is_network_machine": True,
                    "serial_number": printer["serialNumber"]
                }
                self.appendItem(item)
