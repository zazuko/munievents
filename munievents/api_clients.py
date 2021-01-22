# -*- coding: utf-8 -*-
import time
from datetime import date, datetime
from typing import Dict

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from munievents.exceptions import NotFoundError

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

    BASE_URL = None
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

    def getMunicipalEvents(self) -> pd.DataFrame:
        """ Get all municipal events, except for changing kanton/bezirk.
            Events covered are:
                - Namensänderung Gemeinde,
                - Neugründung Gemeinde/Bezirk,
                - Gebietsänderung Gemeinde,
                - Aufhebung Gemeinde/Bezirk,
                - Neue Bezirks-/Kantonszuteilung
            Args:
                None:

            Returns:
                pd.DataFrame:   municipal events. Includes columns:
                                - parent_name,
                                - parent_admission (yyyy),
                                - parent_abolition (yyyy),
                                - child_name,
                                - child_admission (yyyy),
                                - child_abolition (yyyy),
                                - eventdate (yyyy-mm-dd),
                                - ab_label,
                                - ad_label
        """

        query = """
        PREFIX rdfs:   <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX gont: <https://gont.ch/>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX ech71: <http://classifications.data.admin.ch/code/ech0071/>

        SELECT DISTINCT ?parent_name ?parent_admission ?parent_abolition ?child_name ?child_admission ?child_abolition ?eventdate ?ab_label ?ad_label
        WHERE {

        ?event a gont:MunicipalityChangeEvent ;
            gont:id ?eventid ;
            gont:date ?eventdate .

        ?parent a gont:MunicipalityVersion ;
            gont:shortName ?parent_name ;
            gont:abolitionMode ?abolition_mode ;
            gont:abolitionEvent ?event .

        ?child a gont:MunicipalityVersion ;
            gont:shortName ?child_name ;
            gont:admissionMode ?admission_mode ;
            gont:admissionEvent ?event .

        ?parent gont:admissionEvent ?_parent_admission.
        ?_parent_admission gont:date ?__parent_admission.
        ?parent gont:abolitionEvent ?_parent_abolition.
        ?_parent_abolition gont:date ?__parent_abolition.

        ?child gont:admissionEvent ?_child_admission.
        ?_child_admission gont:date ?__child_admission.

        OPTIONAL {
            ?child gont:abolitionEvent ?_child_abolition.
            ?_child_abolition gont:date ?__child_abolition.
            BIND (year(?__child_abolition) AS ?child_abolition).
        }

        ?abolition_mode <http://www.w3.org/2004/02/skos/core#prefLabel> ?ab_label.
        ?admission_mode <http://www.w3.org/2004/02/skos/core#prefLabel> ?ad_label.

        FILTER(?admission_mode IN (ech71:20, ech71:21, ech71:23, ech71:24, ech71:26)).
        FILTER(?abolition_mode IN (ech71:23, ech71:24, ech71:26, ech71:29)).

      	BIND (year(?__parent_abolition) AS ?parent_abolition).
        BIND (year(?__parent_admission) AS ?parent_admission).
        BIND (year(?__child_admission) AS ?child_admission).
        }
        order by ?eventid
        """

        return self.send_query(query)
