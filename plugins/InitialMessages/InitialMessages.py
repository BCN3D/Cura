from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

from UM.Extension import Extension
from UM.Preferences import Preferences
from UM.Message import Message
from UM.Application import Application


class InitialMessages(Extension):

    def __init__(self, parent = None):
        super().__init__()
        Preferences.getInstance().addPreference("cura/info_changed_materials", True)
        Preferences.getInstance().addPreference("cura/first_run", True)
        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalStackChanged)
        self._message = Message("Attention! This version includes the new material profiles. <br/><br/>"
                                "Please consider reading the following information in case you still have remaining stock of ABS or TPU.",
                                title="Important information", lifetime=0)
        self._first_run_message = Message("BCN3D has made a big update on the BCN3D Filaments portfolio, extending the range of technical materials.",
                                          title="BCN3D Filaments update", lifetime=0)

    def _onGlobalStackChanged(self):
        global_stack = Application.getInstance().getGlobalContainerStack()
        if global_stack:
            if Preferences.getInstance().getValue("cura/info_changed_materials"):
                self._message.addAction("open_link", "Read more", None, None)
                self._message.addAction("not_show", "Close and hide", None, None, Message.ActionButtonStyle.LINK)
                self._message.actionTriggered.connect(self._onActionTriggered)
                self._message.show()
            if Preferences.getInstance().getValue("cura/first_run"):
                Preferences.getInstance().setValue("cura/first_run", False)
                self._first_run_message.addAction("filaments", "Read more", None, None)
                self._first_run_message.actionTriggered.connect(self._onActionTriggered)
                self._first_run_message.show()



    def _onActionTriggered(self, message, action):
        if action == "not_show":
            Preferences.getInstance().setValue("cura/info_changed_materials", False)
            message.hide()
        elif action == "open_link":
            QDesktopServices.openUrl(QUrl("https://www.bcn3d.com"))
        elif action == "filaments":
            QDesktopServices.openUrl(QUrl("https://www.bcn3d.com"))
