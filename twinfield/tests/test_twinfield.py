import logging
import os
from xml.etree import ElementTree as Et

from twinfield.tests import tw

tw.offices = ["1060271"]


def test_get_metadata():
    module = "040_1"
    df = tw.metadata(code=module)
    logging.info(f"imported {df.shape[0]} records and {df.shape[1]} columns for module {module}")


def test_module_100():
    module = "100"
    df = tw.query_by_year(code=module, year=2021)
    logging.info(f"imported {df.shape[0]} records and {df.shape[1]} columns for module {module}")


def test_dimensions_deb():
    dim_type = "DEB"
    df = tw.dimensions(dim_type=dim_type)

    logging.info(f"imported {df.shape[0]} records and {df.shape[1]} columns for module {dim_type}")


def test_dimensions_deb_with_addresses():
    dim_type = "DEB"
    df, df_address = tw.dimensions(dim_type=dim_type, addresses=True)

    logging.info(f"imported {df.shape[0]} records and {df.shape[1]} columns for module {dim_type}")
    logging.info(
        f"imported {df_address.shape[0]} records and {df_address.shape[1]} columns for module {dim_type}_address"
    )


def test_dimensions_cred():
    dim_type = "CRD"
    tw.offices = ["1074700"]
    df = tw.dimensions(dim_type=dim_type)

    logging.info(f"imported {df.shape[0]} records and {df.shape[1]} columns for module {dim_type}")


def test_dimensions_cred_with_addresses():
    dim_type = "CRD"
    df, df_address = tw.dimensions(dim_type=dim_type, addresses=True)

    logging.info(f"imported {df.shape[0]} records and {df.shape[1]} columns for module {dim_type}")
    logging.info(
        f"imported {df_address.shape[0]} records and {df_address.shape[1]} columns for module {dim_type}_address"
    )


def test_dimensions_kpl():
    dim_type = "KPL"
    tw.offices = ["1074700"]
    df = tw.dimensions(dim_type=dim_type)

    logging.info(f"imported {df.shape[0]} records and {df.shape[1]} columns for module {dim_type}")


def test_module_030_1():
    module = "030_1"
    df = tw.query_by_year(code=module, year=2021)
    logging.info(f"imported {df.shape[0]} records and {df.shape[1]} columns for module {module}")
    assert df["line.id"].is_unique


def test_module_030_3():
    module = "030_3"
    df = tw.query_by_year(code=module, year=2021)
    logging.info(f"imported {df.shape[0]} records and {df.shape[1]} columns for module {module}")
    assert df["line.id"].is_unique


def test_module_040_1():
    module = "040_1"
    filters = {
        "fin.trs.head.balanceregimeprompt": ["equal", {"from": "generic"}],
    }

    df = tw.query_by_year(code=module, year=2021, filters=filters)
    logging.info(f"imported {df.shape[0]} records and {df.shape[1]} columns for module {module}")


def test_module_with_filter():
    module = "100"
    filters = {"fin.trs.line.matchstatus": ["equal", {"from": "available"}]}
    df = tw.query_by_year(code=module, year=2021, filters=filters)
    logging.info(f"imported {df.shape[0]} records and {df.shape[1]} columns for module {module}")


def test_module_200():
    module = "200"
    df = tw.query_by_year(code=module, year=2021)
    logging.info(f"imported {df.shape[0]} records and {df.shape[1]} columns for module {module}")
    assert df["line.id"].is_unique


def test_login_expired():
    error_xml = Et.parse(os.path.join("data", "invalid_token_response.xml"))
    fault_string = error_xml.find("env:Body/env:Fault/faultstring", tw.namespaces).text
    # refresh the access token if  the token is invalid.
    tw.access_token = tw.refresh_access_token()
    assert fault_string == "Access denied. Token invalid."


def test_delete_module():
    df = tw.deleted(date_from="2022-03-03T00:00:00")
    logging.info(f"imported {df.shape[0]} records and {df.shape[1]} columns for module deleted")


if __name__ == "__main__":
    tw.offices = ["1060271"]
    test_get_metadata()
    test_module_100()
    test_module_200()
    test_module_030_1()
    test_module_040_1()
    test_module_with_filter()
    test_dimensions_deb()
    test_dimensions_deb_with_addresses()
    test_dimensions_cred()
    test_dimensions_cred_with_addresses()
    test_dimensions_kpl()
    test_login_expired()
