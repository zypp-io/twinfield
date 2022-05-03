import base64
import json
import os

import requests

from twinfield.exceptions import EnvironmentVariablesError, LoginSessionError


class TwinfieldLogin:
    def __init__(self):
        self.organisation = os.environ.get("TWINFIELD_ORGANISATION")
        self.client_id = os.environ.get("TWINFIELD_CLIENT_ID")
        self.client_secret = os.environ.get("TWINFIELD_CLIENT_SECRET")
        self.refresh_token = os.environ.get("TWINFIELD_REFRESH_TOKEN")
        self.check_environment_variables()

        self.header = self.create_authorization_header()
        self.cluster = self.determine_cluster()

    def check_environment_variables(self):
        # Test if environment variables are set for Twinfield login

        if not all([self.client_id, self.client_secret, self.organisation, self.refresh_token]):
            raise EnvironmentVariablesError(
                "One of the environment variables TWINFIELD_CLIENT_ID, TWINFIELD_CLIENT_SECRET, "
                "TWINFIELD_ORGANISATION or TWINFIELD_REFRESH_TOKEN is not set"
            )

    def create_authorization_header(self):
        # encode client_id en client_secret to be send as an authorization header in the request.
        raw = f"{self.client_id}:{self.client_secret}".encode("ascii")
        base64_credentials = base64.b64encode(raw).decode("ascii")
        header = {"Content-Type": "application/x-www-form-urlencoded ", "Authorization": f"Basic {base64_credentials}"}

        return header

    def refresh_access_token(self):
        url = "https://login.twinfield.com/auth/authentication/connect/token"
        response = requests.post(
            url=url, headers=self.header, data={"grant_type": "refresh_token", "refresh_token": self.refresh_token}
        )
        if not response:
            raise LoginSessionError("Could not refresh access token")
        json_data = json.loads(response.text)
        access_token = json_data.get("access_token")

        return access_token

    def determine_cluster(self):
        access_token = self.refresh_access_token()
        url = f"https://login.twinfield.com/auth/authentication/connect/accesstokenvalidation?token={access_token}"

        response = requests.get(url=url, headers=self.header)
        json_data = json.loads(response.text)
        cluster = json_data.get("twf.clusterUrl")

        return cluster
