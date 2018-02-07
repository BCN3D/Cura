from PyQt5.QtCore import pyqtSlot, pyqtSignal, pyqtProperty, QObject

from UM.Application import Application
from UM.Logger import Logger
from UM.Message import Message
from UM.i18n import i18nCatalog

from cura.Settings.Bcn3DFixes import Bcn3DFixes

catalog = i18nCatalog("cura")

class PostSlicing(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._bcn3d_fixes_job = None

    @pyqtSlot()
    def applyPostSlice(self):
        if self._bcn3d_fixes_job is not None and self._bcn3d_fixes_job.isRunning():
            return
        container = Application.getInstance().getGlobalContainerStack()
        auto_apply_fixes = container.getProperty("auto_apply_fixes", "value")
        print_mode_enabled = container.getProperty("print_mode", "enabled")
        if not auto_apply_fixes and not print_mode_enabled:
            self._onFinished()
            return
        scene = Application.getInstance().getController().getScene()
        if hasattr(scene, "gcode_list"):
            gcode_list = getattr(scene, "gcode_list")
            if gcode_list:
                if print_mode_enabled and ";MIRROR" not in gcode_list[0] and ";DUPLICATION" not in gcode_list[0]:
                    print_mode = container.getProperty("print_mode", "value")
                    if print_mode == "mirror":
                        gcode_list[0] += ";MIRROR\n"
                        gcode_list[1] += "M605 S6 ;mirror mode enabled\nG4 P1\nG4 P2\nG4 P3\n"
                    elif print_mode == "duplication":
                        gcode_list[0] += ";DUPLICATION\n"
                        gcode_list[1] += "M605 S5 ;duplication mode enabled\nG4 P1\nG4 P2\nG4 P3\n"

                if ";BCN3D_FIXES" not in gcode_list[0] and auto_apply_fixes:
                    self._bcn3d_fixes_job = Bcn3DFixes(container, gcode_list)
                    self._bcn3d_fixes_job.finished.connect(self._onFinished)
                    message = Message(catalog.i18nc("@info:postslice", "Preparing gcode"), progress=-1)
                    message.show()
                    self._bcn3d_fixes_job.setMessage(message)
                    self._bcn3d_fixes_job.start()
                else:
                    self._onFinished()
                    Logger.log("i", "Fixes already applied")
            else:
                self._onFinished()
        else:
            self._onFinished()

    postSlicingFinished = pyqtSignal()

    def _onFinished(self, job=None):
        self.postSlicingFinished.emit()