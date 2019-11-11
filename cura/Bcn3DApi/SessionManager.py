from UM.Preferences import Preferences

import json


class SessionManager:
    bcn3d_auth_data_key = "general/bcn3d_auth_data"

    def __init__(self):
        super().__init__()
        if SessionManager.__instance is not None:
            raise ValueError("Duplicate singleton creation")

        self._access_token = None
        self._refresh_token = None
        self._current_user = None

        self._preferences = Preferences.getInstance()

    def initialize(self):
        self._preferences.addPreference(self.bcn3d_auth_data_key, "{}")
        auth_data = json.loads(self._preferences.getValue(self.bcn3d_auth_data_key))
        self._access_token = auth_data.get("access_token")
        self._refresh_token = auth_data.get("refresh_token")

    def getAccessToken(self):
        return self._access_token

    def getRefreshToken(self):
        return self._refresh_token

    def setAccessToken(self, access_token):
        self._access_token = access_token

    def setRefreshToken(self, refresh_token):
        self._refresh_token = refresh_token

    def storeSession(self):
        self._preferences.setValue(self.bcn3d_auth_data_key, json.dumps(
            {
                "access_token": self._access_token, "refresh_token": self._refresh_token
            }
        ))

    def clearSession(self):
        self._access_token = None
        self._refresh_token = None
        self._current_user = None
        self._preferences.resetPreference(self.bcn3d_auth_data_key)

    @classmethod
    def getInstance(cls) -> "SessionManager":
        if not cls.__instance:
            cls.__instance = SessionManager()
        return cls.__instance

    __instance = None
