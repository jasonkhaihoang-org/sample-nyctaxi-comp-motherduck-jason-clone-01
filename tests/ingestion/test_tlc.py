import io

import pyarrow as pa
import pyarrow.parquet as pq
from sources import tlc


def _parquet_bytes(rows: int) -> bytes:
    table = pa.table({"VendorID": list(range(rows)), "total_amount": [1.5] * rows})
    sink = io.BytesIO()
    pq.write_table(table, sink)
    return sink.getvalue()


def _fetch(url: str) -> bytes:
    if url.endswith("taxi_zone_lookup.csv"):
        return b"LocationID,Borough,Zone,service_zone\n1,EWR,Newark Airport,EWR\n2,Queens,Jamaica Bay,Boro Zone\n"
    return _parquet_bytes(4)


def test_trip_url_format():
    assert (
        tlc.trip_url("yellow", "2024-01")
        == "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet"
    )


def test_months_cover_the_three_month_window():
    assert tlc.MONTHS == ["2024-01", "2024-02", "2024-03"]


def test_source_yields_one_table_per_month():
    source = tlc.tlc_source(fetch=_fetch)
    for resource in ("yellow_tripdata", "green_tripdata"):
        tables = list(source.resources[resource])
        assert len(tables) == 3
        assert all(isinstance(t, pa.Table) for t in tables)


def test_no_rows_dropped_or_changed():
    source = tlc.tlc_source(fetch=_fetch)
    tables = list(source.resources["yellow_tripdata"])
    assert sum(t.num_rows for t in tables) == 12
    assert tables[0].column_names == ["VendorID", "total_amount"]


def test_zone_rows_keep_the_types_the_csv_reader_infers():
    rows = tlc.zone_rows(fetch=_fetch)
    assert rows == [
        {"LocationID": 1, "Borough": "EWR", "Zone": "Newark Airport", "service_zone": "EWR"},
        {"LocationID": 2, "Borough": "Queens", "Zone": "Jamaica Bay", "service_zone": "Boro Zone"},
    ]


def test_source_loads_only_the_months_it_is_given():
    fetched = []

    def fetch(url):
        fetched.append(url)
        return _fetch(url)

    source = tlc.tlc_source(fetch=fetch, months=["2024-01"])
    assert len(list(source.resources["yellow_tripdata"])) == 1
    assert [u for u in fetched if "tripdata" in u] == [tlc.trip_url("yellow", "2024-01")]


def test_months_can_be_set_from_the_environment(monkeypatch):
    monkeypatch.setenv("SOURCES__TLC__MONTHS", '["2024-01"]')
    source = tlc.tlc_source.clone(name="tlc", section="tlc")(fetch=_fetch)
    assert len(list(source.resources["green_tripdata"])) == 1


def _download_row_groups(row_groups: int, rows_per_group: int):
    """A download that writes a Parquet file of the given row groups, recording each URL."""
    urls = []

    def download(url: str, path: str) -> None:
        urls.append(url)
        table = pa.table({"PULocationID": list(range(row_groups * rows_per_group))})
        pq.write_table(table, path, row_group_size=rows_per_group)

    return download, urls


def test_hvfhv_url_format():
    assert (
        tlc.hvfhv_url("2024-01")
        == "https://d37ci6vzurychx.cloudfront.net/trip-data/fhvhv_tripdata_2024-01.parquet"
    )


def test_hvfhv_yields_one_table_per_row_group_and_keeps_every_row():
    download, _ = _download_row_groups(row_groups=3, rows_per_group=4)
    tables = list(tlc.tlc_source(fetch=_fetch, download=download).resources["fhvhv_tripdata"])
    assert [t.num_rows for t in tables] == [4, 4, 4]
    assert pa.concat_tables(tables).column("PULocationID").to_pylist() == list(range(12))


def test_hvfhv_loads_january_2024_only_whatever_the_months_setting(monkeypatch):
    monkeypatch.setenv("SOURCES__TLC__MONTHS", '["2024-01", "2024-02", "2024-03"]')
    download, urls = _download_row_groups(row_groups=1, rows_per_group=2)
    source = tlc.tlc_source.clone(name="tlc", section="tlc")(fetch=_fetch, download=download)
    list(source.resources["fhvhv_tripdata"])
    assert tlc.HVFHV_MONTHS == ["2024-01"]
    assert urls == [tlc.hvfhv_url("2024-01")]
