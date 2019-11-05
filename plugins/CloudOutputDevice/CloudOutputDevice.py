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
        serial_number = Application.getInstance().getGlobalContainerStack().getMetaDataEntry("serial_number")
        if not serial_number:
            self._progress_message.hide()
            Message("The selected printer doesn't support this feature.", title="Can't send gcode to printer").show()
            return
        printer = self._data_api_service.getPrinter(serial_number)
        if not printer:
            self._progress_message.hide()
            Message("The selected printer doesn't exist or you don't have permissions to print.", title="Can't send gcode to printer").show()
            return
        if printer.state != "Idle":
            self._progress_message.hide()
            Message("The selected printer isn't ready to print.", title="Can't send gcode to printer").show()
            return
        self.writeStarted.emit(self)
        active_build_plate = Application.getInstance().getBuildPlateModel().activeBuildPlate
        self._gcode = getattr(Application.getInstance().getController().getScene(), "gcode_dict")[active_build_plate]
        gcode = self._joinGcode()
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.write(gcode.encode())
        temp_file_name = temp_file.name
        temp_file.close()
        file_name_with_extension = file_name + ".gcode.zip"
        gcode_path = os.path.join(tempfile.gettempdir(), file_name_with_extension)
        with ZipFile(gcode_path, "w") as gcode_zip:
            gcode_zip.write(temp_file_name, arcname=file_name + ".gcode")
        self._data_api_service.sendGcode(gcode_path, file_name_with_extension, serial_number)
        os.remove(temp_file_name)
        os.remove(gcode_path)
        self.writeFinished.emit()
        self._progress_message.hide()

    def _joinGcode(self):
        gcode = ""
        for line in self._gcode:
            gcode += line
        return gcode
