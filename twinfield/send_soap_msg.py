import logging
import os
import pickle
from datetime import datetime
from tqdm import tqdm
import pandas as pd
import requests
from azure.storage.blob import BlobServiceClient

from . import responses
from . import templates
from .credentials import twinfield_login
from .exceptions import ServerError
from .functions import select_office, create_dir
from twinfield import TIME_OUT


def save_xml_locally(run_params, response, msg_id) -> tuple:
    """

    Parameters
    ----------
    run_params:  input parameters of script (set at start of script)
    response: xml response from twinfield server
    msg_id: generated id for keeping track of messages

    Returns tuple of the file_path and the filename
    -------

    """

    foldername = datetime.now().strftime("%Y%m%d")
    path = os.path.join(run_params.responsedir, foldername)
    if not os.path.exists(path):
        filedir = create_dir(path)
    else:
        filedir = path
    filename = f"response_{msg_id}_{datetime.now().strftime('%H_%M_%S')}.xml"
    file_path = os.path.join(filedir, filename)
    f = open(file_path, "w")
    f.write(response)
    f.close()

    if run_params.debug:
        filename_blob = os.path.join("xml_responses", "test", foldername, filename)
    else:
        filename_blob = os.path.join("xml_responses", run_params.modules, foldername, filename)

    return file_path, filename_blob


def create_blob_service_client():
    """

    Returns Azure blob service client based on environment credentials
    -------

    """
    name, key = os.environ.get("ls_blob_account_name"), os.environ.get("ls_blob_account_key")
    connect_str = f"DefaultEndpointsProtocol=https;AccountName={name};AccountKey={key}"

    blob_service_client = BlobServiceClient.from_connection_string(connect_str)

    return blob_service_client


def response_to_blob(file_path, filename) -> None:
    """

    Parameters
    ----------
    file_path: file_path of the XML file to be uploaded to the blob storage
    filename: the filename of the XML.

    Returns None. Uploads the XML file to the blob storage.
    -------

    """

    blob_service_client = create_blob_service_client()

    blob_client = blob_service_client.get_blob_client(
        container=os.environ.get("ls_blob_container_name"),
        blob=filename,
    )

    logging.info(f"start uploading blob {filename}...")
    with open(file_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)
    logging.info(f"finished uploading blob {filename}!")


def export_response(run_params, response, msg_id) -> None:
    """

    Parameters
    ----------
    run_params:  input parameters of script (set at start of script)
    response: xml response from the twinfield server
    msg_id: self generated ID to keep track of the messages

    Returns None. Uploads the files to blob storage.
    -------

    """

    file_path, filename = save_xml_locally(run_params, response, msg_id)
    response_to_blob(file_path, filename)


def parse_errors(run_params, data) -> None:
    """

    Parameters
    ----------
    run_params:  input parameters of script (set at start of script)
    data: dataset containing potential errors

    Returns None. Exports errors to a seperate pickle file called 'response_error.pkl'
    -------

    """
    if "msgtype" in data.columns:
        errors = data.loc[data.msgtype == "error"]
        # raise KostenPlaatsError(f"{len(errors)} kostenplaatsen ontbreken in TwinField.")
    else:
        logging.info("geen errors")
        errors = pd.DataFrame()

    errors.to_pickle(os.path.join(run_params.pickledir, "response_errors.pkl"))
    logging.info(f"{len(errors)} errors geexporteerd.")


def get_response(messages, run_params, login) -> pd.DataFrame:
    """

    Parameters
    ----------
    messages: the input XML messages for the twinfield server
    run_params:  input parameters of script (set at start of script)
    login:  login parameters (SessionParameters)

    Returns: dataframe containing all responses from the xml messages
    -------

    """
    ttl = pd.DataFrame()
    msg_id = 0
    for msg in tqdm(messages):
        msg_id += 1

        soap_body = msg.get("xml_msg")
        officecode = msg.get("office_code")
        select_office(officecode=officecode, param=login)

        if run_params.modules == "vrk":
            path_xml = os.path.join("xml_templates", "template_transactions.xml")
            soap_msg = templates.import_xml(path_xml).format(login.session_id, soap_body)
        elif run_params.modules == "ink":
            path_xml = os.path.join("xml_templates", "template_transactions.xml")
            soap_msg = templates.import_xml(path_xml).format(login.session_id, soap_body)
        elif run_params.modules == "memo":
            path_xml = os.path.join("xml_templates", "template_transactions.xml")
            soap_msg = templates.import_xml(path_xml).format(login.session_id, soap_body)
        elif run_params.modules == "ljp":
            path_xml = os.path.join("xml_templates", "template_concept.xml")
            soap_msg = templates.import_xml(path_xml).format(login.session_id, soap_body)
        elif run_params.modules == "salesinvoice":
            path_xml = os.path.join("xml_templates", "template_salesinvoices.xml")
            soap_msg = templates.import_xml(path_xml).format(login.session_id, soap_body)
        elif run_params.modules == "read_dimensions":
            path_xml = os.path.join("xml_templates", "read_dimensions.xml")
            soap_msg = templates.import_xml(path_xml).format(login.session_id, msg.get("dim_type"))
        elif run_params.modules == "upload_dimensions":
            path_xml = os.path.join("xml_templates", "upload_dimensions.xml")
            soap_msg = templates.import_xml(path_xml).format(login.session_id, soap_body)
        else:
            raise ServerError(f"geen routine voor {run_params.modules}")

        url = f"https://{login.cluster}.twinfield.com/webservices/processxml.asmx?wsdl"
        response = requests.post(url=url, headers=login.header, data=soap_msg.encode("utf16"), timeout=TIME_OUT)

        if run_params.modules != "read_dimensions" and run_params.modules != "upload_dimensions":
            export_response(run_params, response.text, msg_id)

        data = responses.parse_response(run_params, response, login)
        data["msg_id"] = msg_id
        ttl = pd.concat([ttl, data], sort=False, ignore_index=True)

    export_response_data(ttl, run_params)

    # send_insert_message(table=ttl, messages=messages, run_params=run_params)

    return ttl


def export_response_data(df, run_params) -> None:
    """

    Parameters
    ----------
    df: dataframe containing responses
    run_params:  input parameters of script (set at start of script)

    Returns None. exports to a pickle file in the tmp directory
    -------

    """
    if run_params.modules == "upload_dimensions":
        return None

    df["rundate"] = run_params.starttijd
    df["kenmerk"] = run_params.modules

    if run_params.modules == "read_dimensions":
        filename = "response_data.pkl"
    else:
        filename = f"response_data_{run_params.starttijd.strftime('%Y%m%d%H%M')}.pkl"

    df.to_pickle(os.path.join(run_params.pickledir, filename))


def upload_soap(run_params, messages) -> pd.DataFrame:
    """

    Parameters
    ----------
    run_params:  input parameters of script (set at start of script)
    messages: the input XML messages for the twinfield server

    Returns dataframe of the Twinfield responses
    -------

    """
    login = twinfield_login()

    if run_params.upload:
        r = get_response(messages, run_params, login)

        parse_errors(run_params, r)
        logging.info("de soap messages zijn verstuurd!")

    else:
        r = pd.DataFrame()
        logging.info("uploaden staat uit.")

    return r


def run(run_params) -> pd.DataFrame:
    """

    Parameters
    ----------
    run_params:  input parameters of script (set at start of script)

    Returns dataframe of the Twinfield responses
    -------

    """
    with open(os.path.join(run_params.pickledir, "messages.pkl"), "rb") as f:
        messages = pickle.load(f)

    r = upload_soap(run_params, messages)

    return r
