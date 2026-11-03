"""NYC TLC open data: yellow and green trip files, the high-volume for-hire (HVFHV) trip file and the zone lookup.

Fetched from the public TLC CDN for the three-month window below, or the months
given in `[sources.tlc] months` (env `SOURCES__TLC__MONTHS`). HVFHV keeps its own
window, `HVFHV_MONTHS`, whatever that setting says (design record D-08). Nothing is
cast, filtered or sampled: each resource yields what the source file holds.
"""

from __future__ import annotations

import io
import tempfile
from typing import Callable, Iterator

import dlt
import pyarrow.csv as pacsv
import pyarrow.parquet as pq
import requests

BASE_URL = "https://d37ci6vzurychx.cloudfront.net"
MONTHS = ["2024-01", "2024-02", "2024-03"]
FLEETS = ("yellow", "green")
# The user chose January 2024 only for HVFHV (design record D-08).
HVFHV_MONTHS = ["2024-01"]

Fetch = Callable[[str], bytes]
# Writes the file at a URL to a local path.
Download = Callable[[str, str], None]


def trip_url(fleet: str, month: str) -> str:
    return f"{BASE_URL}/trip-data/{fleet}_tripdata_{month}.parquet"


def hvfhv_url(month: str) -> str:
    return f"{BASE_URL}/trip-data/fhvhv_tripdata_{month}.parquet"


def zone_url() -> str:
    return f"{BASE_URL}/misc/taxi_zone_lookup.csv"


def http_get(url: str) -> bytes:
    response = requests.get(url, timeout=300)
    response.raise_for_status()
    return response.content


def http_download(url: str, path: str) -> None:
    with requests.get(url, stream=True, timeout=300) as response:
        response.raise_for_status()
        with open(path, "wb") as out:
            for chunk in response.iter_content(chunk_size=8 * 1024 * 1024):
                out.write(chunk)


def row_group_tables(url: str, download: Download = http_download) -> Iterator:
    """One table per Parquet row group, so memory holds one row group, never the whole file (D-10)."""
    with tempfile.TemporaryDirectory() as directory:
        path = f"{directory}/file.parquet"
        download(url, path)
        parquet = pq.ParquetFile(path)
        for index in range(parquet.num_row_groups):
            yield parquet.read_row_group(index)


def zone_rows(fetch: Fetch = http_get) -> list[dict]:
    """The TLC zone lookup, one dict per row, with the types the CSV reader infers."""
    return pacsv.read_csv(io.BytesIO(fetch(zone_url()))).to_pylist()


def trip_tables(fleet: str, fetch: Fetch = http_get, months: list[str] = MONTHS) -> Iterator:
    for month in months:
        yield pq.read_table(io.BytesIO(fetch(trip_url(fleet, month))))


@dlt.source(name="tlc")
def tlc_source(fetch: Fetch = http_get, months: list[str] | None = None, download: Download = http_download):
    months = months or MONTHS

    @dlt.resource(name="yellow_tripdata")
    def yellow_tripdata():
        yield from trip_tables("yellow", fetch, months)

    @dlt.resource(name="green_tripdata")
    def green_tripdata():
        yield from trip_tables("green", fetch, months)

    @dlt.resource(name="taxi_zone_lookup")
    def taxi_zone_lookup():
        yield zone_rows(fetch)

    @dlt.resource(name="fhvhv_tripdata")
    def fhvhv_tripdata():
        for month in HVFHV_MONTHS:
            yield from row_group_tables(hvfhv_url(month), download)

    return yellow_tripdata, green_tripdata, fhvhv_tripdata, taxi_zone_lookup
