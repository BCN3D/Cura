from UM.Application import Application
from UM.OutputDevice.OutputDevice import OutputDevice
from UM.Message import Message

from cura.Bcn3DApi.DataApiService import DataApiService

import tempfile
import os
from zipfile import ZipFile

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


class CloudOutputDevice(OutputDevice):
    def __init__(self):
        super().__init__("cloud")

        self.setName(catalog.i18nc("@item:inmenu", "Cloud"))
        self.setShortDescription(catalog.i18nc("@action:button Preceded by 'Ready to'.", "Send to Printer"))
        self.setDescription(catalog.i18nc("@info:tooltip", "Send to Printer"))
        self.setIconName("cloud")

        self._data_api_service = DataApiService.getInstance()

        self._gcode = []
        self._writing = False
        self._compressing_gcode = False
        self._progress_message = Message("Sending the gcode to the printer",
                                         title="Send to Printer", dismissable=False, progress=-1)

    def requestWrite(self, nodes, file_name=None, limit_mimetypes=False, file_handler=None, **kwargs):
        self._progress_message.show()
        self.writeStarted.emit(self)
        active_build_plate = Application.getInstance().getBuildPlateModel().activeBuildPlate
        self._gcode = getattr(Application.getInstance().getController().getScene(), "gcode_dict")[active_build_plate]
        gcode = self._joinGcode()
        temp_file = tempfile.NamedTemporaryFile()
        temp_folder_path = os.path.dirname(temp_file)
        if not os.path.exists(temp_folder_path):
            os.makedirs(temp_folder_path, 0o0755)
        temp_file.write(gcode.encode())
        file_name_with_extension = file_name + ".gcode.zip"
        gcode_path = os.path.join(tempfile.gettempdir(), file_name_with_extension)
        with ZipFile(gcode_path, "w") as gcode_zip:
            gcode_zip.write(temp_file.name, arcname=file_name + ".gcode")
        self._data_api_service.sendGcode(gcode_path, file_name_with_extension)
        self.writeFinished.emit()
        self._progress_message.hide()

    def _joinGcode(self):
        gcode = ""
        for line in self._gcode:
            gcode += line
        return gcode
