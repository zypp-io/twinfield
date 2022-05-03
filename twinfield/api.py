import logging
from datetime import datetime

import pandas as pd
from tqdm import tqdm

from twinfield.browse import Browse
from twinfield.core import Base
from twinfield.dimensions import Dimensions
from twinfield.metadata import Metadata
from twinfield.offices import Offices


class TwinfieldApi(Base):
    def __init__(self):
        """
        Base class for working with the Twinfield API. from this class it's possible to create requests for the modules
         browse ,dimensions, metadata and offices. The function query by year makes it possible to automatically import
         a full year of data.
        """

        super().__init__()
        self.offices = self.list_offices().index.tolist()

    def list_offices(self) -> pd.DataFrame:
        offices = Offices(access_token=self.refresh_access_token(), cluster=self.cluster)
        offices_df = offices.list_offices()

        return offices_df

    def select_office(self, officecode):
        """

        Parameters
        ----------
        officecode: office code that needs to be selected

        Returns
        -------
        None
            selects the office.
        """

        offices = Offices(access_token=self.refresh_access_token(), cluster=self.cluster)
        offices.select(officecode=officecode)

    @staticmethod
    def browse(code: str, fields: list, filters: dict, company: str, metadata: pd.DataFrame) -> pd.DataFrame:
        """

        Parameters
        ----------
        code: str
            specific browsecode for request (e.g. 100)
        fields: list
            list of fields for the dataset
        filters: dict
            dictionary containing specific fields that need to be filtered.
        company: str
            company code (office) for request
        metadata: pd.DataFrame
            dataframe containing field information.
        Returns
        -------
        df: pd.DataFrame
            dataframe containing browse data
        """

        # construct the request in the Browse class
        browse = Browse(
            code=code,
            fields=fields,
            filters=filters,
            company=company,
            metadata=metadata,
        )
        # send the request.
        response = browse.send_request(browse=browse)
        df = browse.parse_response(response)

        return df

    def dimensions(self, dim_type: str, addresses: bool = False):
        """

        Parameters
        ----------
        dim_type: str
            specific dimension type.
        addresses: bool
            indicator for pulling the addresses for each dimension. default = False
        Returns
        -------
        df: pd.DataFrame
            dataframe containing dimensions data
        """
        df_list = []
        if addresses:
            adress_df_list = []
        for company in tqdm(self.offices, desc=f"importing dimensions {dim_type}..."):
            # construct the request in the Browse class
            dim = Dimensions(dim_type=dim_type, company=company)
            # send the request.
            response = dim.send_request(browse=dim)
            df = dim.parse_response_dimensions(response)
            df_list.append(df)

            if addresses:
                df_address = dim.parse_response_dimension_addresses(response)
                adress_df_list.append(df_address)  # noqa

        df = pd.concat(df_list)

        if addresses:
            return (df, pd.concat(adress_df_list))  # noqa
        else:
            return df

    def dimension_addresses(self, dim_type: str) -> pd.DataFrame:
        """

        Parameters
        ----------
        dim_type: str
            specific dimension type.
        Returns
        -------
        df: pd.DataFrame
            dataframe containing dimensions data
        """
        df_list = []

        for company in tqdm(self.offices, desc=f"importing dimensions {dim_type}..."):
            # construct the request in the Browse class
            dim = Dimensions(dim_type=dim_type, company=company)
            # send the request.
            response = dim.send_request(browse=dim)
            df = dim.parse_response_dimension_addresses(response)

            df_list.append(df)

        df = pd.concat(df_list)

        return df

    def metadata(self, code: str) -> pd.DataFrame:
        metadata = Metadata(code=code, company=self.offices[0])
        df = metadata.send_request(cluster=self.cluster)

        return df

    @staticmethod
    def chunks(lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i : i + n]  # noqa

    def generate_periodbatches(self, year_from: int = None, year_to: int = None, batchsize: int = 1):

        if not year_from:
            year_from = datetime.now().year - 1  # last year
        if not year_to:
            year_to = datetime.now().year  # this year
        periods = [
            "00",
            "01",
            "02",
            "03",
            "04",
            "05",
            "06",
            "07",
            "08",
            "09",
            "10",
            "11",
            "12",
            "13",
            "55",
        ]
        years = list(range(year_from, year_to + 1))

        filters = []
        for year in years:
            for period in self.chunks(periods, batchsize):
                period_filter = {"from": f"{year}/{period[0]}", "to": f"{year}/{period[-1]}"}
                filters.append(period_filter)

        return filters

    def query_by_year(self, code: str, year: int, fields: list = None, batchsize: int = 1, filters: dict = None):

        metadata = self.metadata(code)
        batches = self.generate_periodbatches(year_from=year, year_to=year, batchsize=batchsize)
        if not filters:
            filters = {}

        if not fields:
            fields = metadata.index.tolist()

        df_list = []
        pbar = tqdm(self.offices, desc=f"importing module {code}...")
        for office in pbar:
            # self.select_office(office)
            for batch in batches:
                # logging.debug(f"requesting {office} - {batch}...")
                pbar.set_description(f"importing module {code} - {office} - {batch}...")
                period_filters = {"fin.trs.head.yearperiod": ("between", batch)}
                filters = {**filters, **period_filters}
                df = self.browse(code=code, fields=fields, filters=filters, company=office, metadata=metadata)
                df_list.append(df)

        df = pd.concat(df_list)

        return df
