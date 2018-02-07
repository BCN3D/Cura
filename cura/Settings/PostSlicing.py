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
        # auto_apply_fixes = container.getProperty("auto_apply_fixes", "value")
        auto_apply_fixes = True
        # if not auto_apply_fixes:
        #     self._onFinished()
        #     return
        scene = Application.getInstance().getController().getScene()
        if hasattr(scene, "gcode_dict"):
            gcode_dict = getattr(scene, "gcode_dict")
            if gcode_dict:
                job_called = False
                for i in gcode_dict:
                    if ";BCN3D_FIXES" not in gcode_dict[i][0] and auto_apply_fixes:
                        self._bcn3d_fixes_job = Bcn3DFixes(container, gcode_dict[i])
                        self._bcn3d_fixes_job.finished.connect(self._onFinished)
                        message = Message(catalog.i18nc("@info:postslice", "Preparing gcode"), progress=-1)
                        message.show()
                        self._bcn3d_fixes_job.setMessage(message)
                        self._bcn3d_fixes_job.start()
                        job_called = True
                else:
                    if not job_called:
                        self._onFinished()
            else:
                self._onFinished()
        else:
            self._onFinished()

    postSlicingFinished = pyqtSignal()

    def _onFinished(self, job=None):
        self.postSlicingFinished.emit()