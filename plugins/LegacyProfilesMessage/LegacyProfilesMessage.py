from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

from UM.Extension import Extension
from UM.Preferences import Preferences
from UM.Message import Message
from UM.Application import Application


class LegacyProfilesMessage(Extension):

    def __init__(self, parent = None):
        super().__init__()
        Preferences.getInstance().addPreference("cura/info_changed_materials", True)
        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalStackChanged)
        self._message = Message("Lorem ipsum dolor sit amet, eiusmod tempor ut labore et dolore magna aliqua.", title="Lorem Ipsum", lifetime=0)

    def _onGlobalStackChanged(self):
        if Preferences.getInstance().getValue("cura/info_changed_materials"):
            global_stack = Application.getInstance().getGlobalContainerStack()
            if global_stack:
                self._message.addAction("open_link", "Profiles Guide", None, None, Message.ActionButtonStyle.LINK)
                self._message.addAction("not_show", "Don't show again", None, None, Message.ActionButtonStyle.LINK)
                self._message.actionTriggered.connect(self._onActionTriggered)
                self._message.show()

    def _onActionTriggered(self, message, action):
        if action == "not_show":
            Preferences.getInstance().setValue("cura/info_changed_materials", False)
            message.hide()
        elif action == "open_link":
            QDesktopServices.openUrl(QUrl("https://www.bcn3d.com"))
