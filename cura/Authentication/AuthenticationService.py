from PyQt5.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal
from UM.Message import Message

import requests


class AuthenticationService(QObject):
    api_url = "https://5zkg780dt3.execute-api.eu-west-1.amazonaws.com/dev"
    onAuthStateChanged = pyqtSignal(bool)

    def __init__(self):
        super().__init__()

        self._access_token = None
        self._refresh_token = None

        self._email = None
        self._is_logged_in = False

    @pyqtProperty(str, notify=onAuthStateChanged)
    def email(self):
        return self._email

    @pyqtProperty(bool, notify=onAuthStateChanged)
    def isLoggedIn(self):
        return self._is_logged_in

    @pyqtSlot(str, str, result=bool)
    def signIn(self, email, password):
        self._email = email
        data = {"email": email, "password": password}
        response = requests.post(self.api_url + "/sign_in", json=data)
        if response.status_code == 200:
            response_message = response.json()
            self._access_token = response_message["accessToken"]
            self._refresh_token = response_message["refreshToken"]
            self.onAuthStateChanged.emit(True)
            message = Message("Now you can print through the cloud!", title="Sign In successfully")
            message.show()
            self._is_logged_in = True
            return True
        else:
            return False

    @pyqtSlot(result=bool)
    def signOut(self):
        headers = {"Authorization": "Bearer {}".format(self._access_token)}
        response = requests.post(self.api_url + "/sign_out", headers=headers)
        if response.status_code == 200:
            self._access_token = None
            self._refresh_token = None
            self._email = None
            self.onAuthStateChanged.emit(False)
            return True
        else:
            return False

    def sendGcode(self, gcode_path, gcode_name):
        headers = {"Authorization": "Bearer {}".format(self._access_token)}
        files = {"file": (gcode_path, open(gcode_path, "rb"))}
        data = {"serialNumber": "xxxxxx", "fileName": gcode_name}
        response = requests.post(self.api_url + "/gcodes", json=data, headers=headers)
        if response.status_code == 200:
            response_message = response.json()
            presigned_url = response_message["url"]
            fields = response_message["fields"]
            response2 = requests.post(presigned_url, data=fields, files=files)


    __instance = None

    @classmethod
    def getInstance(cls) -> "AuthenticationService":
        if not cls.__instance:
            cls.__instance = AuthenticationService()
        return cls.__instance
