from PyQt5.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal
from UM.Message import Message

import requests


class AuthApiService(QObject):
    api_url = "https://5zkg780dt3.execute-api.eu-west-1.amazonaws.com/dev"
    onAuthStateChanged = pyqtSignal(bool)

    def __init__(self):
        super().__init__()

        self._access_token = None
        self._refresh_token = None

        self._email = None
        self._is_logged_in = False

    def getAccessToken(self):
        return self._access_token

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
        if 200 <= response.status_code < 300:
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
        if 200 <= response.status_code < 300:
            self._access_token = None
            self._refresh_token = None
            self._email = None
            self.onAuthStateChanged.emit(False)
            return True
        else:
            return False

    __instance = None

    @classmethod
    def getInstance(cls) -> "AuthApiService":
        if not cls.__instance:
            cls.__instance = AuthApiService()
        return cls.__instance
