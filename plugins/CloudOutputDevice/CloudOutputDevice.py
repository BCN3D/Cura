from UM.Application import Application
from UM.OutputDevice.OutputDevice import OutputDevice
from UM.Message import Message

from cura.Authentication.AuthenticationService import AuthenticationService

from PyQt5.QtCore import QCoreApplication
from typing import Optional
import gzip
import sys
import tempfile
from zipfile import ZipFile

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


class CloudOutputDevice(OutputDevice):
    def __init__(self):
        super().__init__("cloud")

        self.setName(catalog.i18nc("@item:inmenu", "Cloud"))
        self.setShortDescription(catalog.i18nc("@action:button Preceded by 'Ready to'.", "Send to cloud"))
        self.setDescription(catalog.i18nc("@info:tooltip", "Send to cloud"))
        self.setIconName("cloud")

        self._auth_service = AuthenticationService.getInstance()

        self._gcode = []
        self._writing = False
        self._compressing_gcode = False
        self._progress_message = Message("Compressing gcode to send", dismissable=False, title="Compressing gcode")

    def requestWrite(self, nodes, file_name=None, limit_mimetypes=False, file_handler=None, **kwargs):
        self._progress_message.show()
        self.writeStarted.emit(self)
        active_build_plate = Application.getInstance().getBuildPlateModel().activeBuildPlate
        self._gcode = getattr(Application.getInstance().getController().getScene(), "gcode_dict")[active_build_plate]
        gcode = self._joinGcode()
        gcode_path = tempfile.gettempdir() + "/temp.gcode.gz"
        with gzip.open(gcode_path, "wb") as gcode_file:
            gcode_file.write(gcode.encode())
        self._auth_service.sendGcode(gcode_path, "temp.gcode.gz")
        self.writeFinished.emit()

    def _joinGcode(self):
        gcode = ""
        for line in self._gcode:
            gcode += line
        return gcode
