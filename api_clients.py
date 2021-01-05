# -*- coding: utf-8 -*-
import time
from datetime import date, datetime
from typing import Dict

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from exceptions import NotFoundError
import pandas as pd

XML_TYPES_TO_PYTHON_CLS = {
    "http://www.w3.org/2001/XMLSchema#integer": int,
    "http://www.w3.org/2001/XMLSchema#float": float,
    "http://www.w3.org/2001/XMLSchema#decimal": float,
    "http://www.w3.org/2001/XMLSchema#date": date.fromisoformat,
    "http://www.w3.org/2001/XMLSchema#dateTime": (lambda x: datetime.strptime(x, "%Y-%m-%dT%H:%M:%SZ")),
}


def requests_retry_session(
    retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504), session=None
):

    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


class SparqlClient:

    last_request = 0
    HEADERS = {
        'Accept': 'application/sparql-results+json',
    }

    def send_query(self, query: str) -> pd.DataFrame:
        """Send SPARQL query. Transform results to pd.DataFrame.
            Args:
                query: 				full SPARQL query

            Returns
                pd.DataFrame	    query results
        """

        session = requests_retry_session()
        request = {"query": query}

        if time.time() < self.last_request + 1:
            time.sleep(1)
        self.last_request = time.time()

        response = session.get(self.BASE_URL, headers=self.HEADERS, params=request)
        response.raise_for_status()
        response = response.json()

        if len(response) == 0:
            raise NotFoundError()

        return self.__normalize_results(response)


    def __normalize_results(self, response: Dict) -> pd.DataFrame:
        """Normalize response from SPARQL endpoint. Transform json structure to table. Convert observations to python data types.
            Args:
                response: 			raw response from SPARQL endpoint

            Returns
                pd.DataFrame	    response from SPARQL endpoint in a tabular form, with python data types
        """

        cols = response["head"]["vars"]
        data = dict(zip(cols, [[] for i in range(len(cols))]))

        for row in response["results"]["bindings"]:
            for key in cols:

                if key in row:

                    value = row[key]["value"]
                    if 'datatype' in row[key]:
                        datatype = row[key]['datatype']
                        value = XML_TYPES_TO_PYTHON_CLS[datatype](value)
                else:
                    value = None

                data[key].append(value)

        df = pd.DataFrame.from_dict(data)
        return df


class Classifications(SparqlClient):

    BASE_URL = "http://classifications.data.admin.ch/query"

    def getMunicipalEvents(self):

        query = """
        PREFIX rdfs:   <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX gont: <https://gont.ch/>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX ech71: <http://classifications.data.admin.ch/code/ech0071/>

        SELECT ?new_commune ?old_commune ?eventdate ?ab_label ?ad_label ?abolition_mode ?admission_mode

        WHERE {

        ?event a gont:MunicipalityChangeEvent ;
            gont:id ?eventid ;
            gont:date ?eventdate .

            ?parent a gont:MunicipalityVersion ;
            gont:shortName ?new_commune ;
            gont:abolitionMode ?abolition_mode ;
            gont:abolitionEvent ?event .

            ?child a gont:MunicipalityVersion ;
            gont:shortName ?old_commune ;
            gont:admissionMode ?admission_mode ;
            gont:admissionEvent ?event .

            ?abolition_mode <http://www.w3.org/2004/02/skos/core#prefLabel> ?ab_label.
            ?admission_mode <http://www.w3.org/2004/02/skos/core#prefLabel> ?ad_label.

        FILTER(?admission_mode IN (ech71:20, ech71:21, ech71:23, ech71:24, ech71:26)).
        FILTER(?abolition_mode IN (ech71:23, ech71:24, ech71:26, ech71:29)).
        }
        ORDER BY ?eventid
        """

        return self.send_query(query)