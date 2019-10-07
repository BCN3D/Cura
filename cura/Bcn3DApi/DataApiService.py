from UM.Message import Message

import requests

from .AuthApiService import AuthApiService


class DataApiService:
    data_api_url = "https://i0fsfve8ha.execute-api.eu-west-1.amazonaws.com/dev"

    def __init__(self):
        super().__init__()
        if DataApiService._instance is not None:
            raise ValueError("Duplicate singleton creation")

        DataApiService._instance = self
        self._auth_api_service = AuthApiService.getInstance()

    def sendGcode(self, gcode_path, gcode_name):
        headers = {"Authorization": "Bearer {}".format(self._auth_api_service.getAccessToken())}
        files = {"file": (gcode_path, open(gcode_path, "rb"))}
        data = {"serialNumber": "000_000000_0000", "fileName": gcode_name}
        response = requests.post(self.data_api_url + "/gcodes", json=data, headers=headers)
        if 200 <= response.status_code < 300:
            response_message = response.json()
            presigned_url = response_message["url"]
            fields = response_message["fields"]
            response2 = requests.post(presigned_url, data=fields, files=files)
            if 200 <= response2.status_code < 300:
                message = Message("The gcode has been sent to the cloud successfully", title="Gcode sent")
                message.show()
            else:
                message = Message("There was an error sending the gcode to the cloud", title="Gcode sent error")
                message.show()
        else:
            message = Message("There was an error sending the gcode to the cloud", title="Gcode sent error")
            message.show()

    @classmethod
    def getInstance(cls):
        if not DataApiService._instance:
            DataApiService._instance = cls()

        return DataApiService._instance

    _instance = None
