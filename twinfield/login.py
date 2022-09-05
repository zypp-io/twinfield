import base64
import json
import logging
import os
import time

import requests
from requests.exceptions import SSLError

from twinfield.exceptions import EnvironmentVariablesError


class TwinfieldLogin:
    def __init__(self):
        self.max_retries = 5
        self.sec_wait = 10
        self.organisation = os.environ.get("TWINFIELD_ORGANISATION")
        self.client_id = os.environ.get("TWINFIELD_CLIENT_ID")
        self.client_secret = os.environ.get("TWINFIELD_CLIENT_SECRET")
        self.refresh_token = os.environ.get("TWINFIELD_REFRESH_TOKEN")
        self.check_environment_variables()

        self.header = self.create_authorization_header()
        self.cluster = self.determine_cluster()

        self.access_token = self.refresh_access_token()

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
        data = {"grant_type": "refresh_token", "refresh_token": self.refresh_token}
        response = self.do_request(url=url, headers=self.header, data=data)

        json_data = json.loads(response.text)
        access_token = json_data.get("access_token")
        return access_token

    def determine_cluster(self):
        access_token = self.refresh_access_token()
        url = f"https://login.twinfield.com/auth/authentication/connect/accesstokenvalidation?token={access_token}"
        response = self.do_request(url=url, headers=self.header, req_type="GET")
        json_data = json.loads(response.text)
        cluster = json_data.get("twf.clusterUrl")
        if not cluster:
            raise ValueError(f"could not retrieve cluster, message from server: {response.text}")

        return cluster

    def do_request(self, url: str, headers: dict, data=None, req_type: str = "POST"):
        """
        Function that executes a request (either POST or GET). It tries
        to do a requests while not yet a success. There is maximum of self.max_retries
        If there is no reaction from the API, the function waits and tries again
        Parameters
        ----------
        url: str
            String with the url to do the request to
        headers: dict
            Dictionary with the header information for the request
        data:
            Data that is sent with the post request (None in case of get request)
        req_type: str
            The request type, POST or GET
        Returns
        -------
        output
            The response of the API request
        """
        success = False
        retry = 0
        login_request = "https://login.twinfield.com/auth/authentication/connect" in url
        while not success:
            if retry > self.max_retries:
                logging.warning(f"Max retries ({self.max_retries}) exceeded, stopping requests for this office.")
                break
            try:
                # start of the request
                if req_type == "POST":
                    with requests.post(url=url, headers=headers, data=data) as response:
                        output = response
                else:
                    with requests.get(url=url, headers=headers) as response:
                        output = response
                success = True

            except (ConnectionError, SSLError) as e:
                retry += 1
                logging.exception(
                    f"No response or error, retrying in {self.sec_wait} seconds. "
                    f"Retry number: {retry}. Error message: {e}"
                )
                time.sleep(self.sec_wait)
                # failed request, retry with new login. Do not do when making login requests
                if not login_request:
                    self.cluster = self.determine_cluster()
        return output
