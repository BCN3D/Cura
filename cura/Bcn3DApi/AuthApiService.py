from PyQt5.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal

from UM.Message import Message

from .SessionManager import SessionManager

import requests
import json


class AuthApiService(QObject):
    api_url = "https://xwicf69omc.execute-api.eu-west-1.amazonaws.com/dev"
    authStateChanged = pyqtSignal(bool, arguments=["isLoggedIn"])

    def __init__(self):
        super().__init__()
        if AuthApiService.__instance is not None:
            raise ValueError("Duplicate singleton creation")

        self._email = None
        self._is_logged_in = False
        self._session_manager = SessionManager.getInstance()
        self._session_manager.initialize()

        if self._session_manager.getAccessToken():
            if self.isValidtoken():
                current_user = self.getCurrentUser()
                self._email = current_user["email"]
                self._is_logged_in = True
                self.authStateChanged.emit(True)

    @pyqtProperty(str, notify=authStateChanged)
    def email(self):
        return self._email

    @pyqtProperty(bool, notify=authStateChanged)
    def isLoggedIn(self):
        return self._is_logged_in

    def getCurrentUser(self):
        headers = {"Authorization": "Bearer {}".format(self._session_manager.getAccessToken())}
        response = requests.get(self.api_url + "/user_data", headers=headers)
        if 200 <= response.status_code < 300:
            return response.json()
        else:
            return {}

    def isValidtoken(self):
        headers = {"Authorization": "Bearer {}".format(self._session_manager.getAccessToken())}
        response = requests.post(self.api_url + "/check_token", json={}, headers=headers)
        if 200 <= response.status_code < 300:
            return True
        else:
            data = {"refresh_token": self._session_manager.getRefreshToken()}
            refresh_response = requests.post(self.api_url + "/refresh:token", json=data)
            if 200 <= refresh_response.status_code < 300:
                refresh_response_message = refresh_response.json()
                self._session_manager.setAccessToken(refresh_response_message["accessToken"])
                self._session_manager.setRefreshToken(refresh_response_message["refreshToken"])
                return True
            else:
                return False

    @pyqtSlot(str, str, result=bool)
    def signIn(self, email, password):
        self._email = email
        data = {"email": email, "password": password}
        response = requests.post(self.api_url + "/sign_in", json=data)
        if 200 <= response.status_code < 300:
            response_message = response.json()
            self._session_manager.setAccessToken(response_message["accessToken"])
            self._session_manager.setRefreshToken(response_message["refreshToken"])
            self._is_logged_in = True
            self.authStateChanged.emit(True)
            message = Message("Now you can print through the cloud!", title="Sign In successfully")
            message.show()
            self._session_manager.storeSession()
            return True
        else:
            return False

    @pyqtSlot(result=bool)
    def signOut(self):
        headers = {"Authorization": "Bearer {}".format(self._session_manager.getAccessToken())}
        response = requests.post(self.api_url + "/sign_out", headers=headers)
        if 200 <= response.status_code < 300:
            self._session_manager.clearSession()
            self._email = None
            self.authStateChanged.emit(False)
            return True
        else:
            return False

    @classmethod
    def getInstance(cls) -> "AuthApiService":
        if not cls.__instance:
            cls.__instance = AuthApiService()
        return cls.__instance

    __instance = None
