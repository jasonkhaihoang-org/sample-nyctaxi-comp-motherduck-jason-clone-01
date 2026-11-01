"""Tests for the semantic query compiler and the generated content test (no warehouse needed)."""

import json
import sys
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

SKILL_SCRIPTS = Path(__file__).resolve().parent.parent / ".agents" / "skills" / "semantic-model" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

import ossie_sql  # noqa: E402
from ossie import app  # noqa: E402
from ossie_compile import CompileError, Model, Query, compile_query  # noqa: E402

RUNNER = CliRunner()
TRIPS = Path("logical-model/nyc_taxi_analytics.ossie.yaml")
FLEET = Path("logical-model/nyc_taxi_fleet.ossie.yaml")
WINDOW = "pickup_date >= DATE '2024-01-01' AND pickup_date < DATE '2024-04-01'"


def _model(path=TRIPS):
    doc = yaml.safe_load(path.read_text())
    return Model(doc, lambda t: t["source"])


def _compile(metrics, group_by=(), filter=None, source=None, path=TRIPS):
    return compile_query(_model(path), Query(list(metrics), list(group_by), filter, source))


def test_conjuncts_are_canonical():
    assert ossie_sql.conjuncts("a IS NOT NULL and b > 1") == ossie_sql.conjuncts("a is not null AND b>1")
    assert ossie_sql.conjuncts("D >= DATE '2024-01-01'") == ossie_sql.conjuncts("d >= date '2024-01-01'")
    assert ossie_sql.conjuncts(None) == []


def test_aggregate_answers_when_the_filter_implies_its_content():
    result = _compile(["trip_count"], [{"via": "trips_to_date", "level": "month"}],
                      WINDOW + " AND pickup_zone_key IS NOT NULL")
    assert result.source == "LTS2_zone_day_agg"
    assert "sum(a.trip_count)" in result.sql


def test_detail_answers_without_the_content_filter():
    """No aggregate holds trips outside the reporting window, so an unfiltered count is the detail's."""
    result = _compile(["trip_count"], [{"via": "trips_to_date", "level": "month"}])
    assert result.source == "LTS1_detail"
    reasons = ("content filter", "holds no level", "not navigable", "binds no column")
    assert all(any(r in why for r in reasons) for why in result.rejected.values()), result.rejected
    assert "content filter" in result.rejected["LTS2_zone_day_agg"]


def test_coarser_level_rolls_up_through_the_dimension():
    result = _compile(["trip_count"], [{"via": "trips_to_date", "level": "quarter"}],
                      WINDOW + " AND pickup_zone_key IS NOT NULL")
    assert result.source == "LTS2_zone_day_agg"
    assert "select distinct" in result.sql and "calendar_year" in result.sql


def test_versioned_dimension_never_rolls_up_from_an_aggregate():
    result = _compile(["trip_count"], [{"via": "trips_to_pickup_zone", "level": "region"}], WINDOW)
    assert result.source == "LTS1_detail"
    assert "versioned" in result.rejected["LTS4_band_profile"]


def test_exact_level_on_a_versioned_dimension_is_held():
    result = _compile(["trip_count"], [{"via": "trips_to_pickup_zone", "level": "borough"}], WINDOW)
    assert result.source == "LTS4_band_profile"


def test_non_navigable_source_is_never_chosen_unasked():
    od = [{"via": "trips_to_pickup_zone", "level": "zone"}, {"via": "trips_to_dropoff_zone", "level": "zone"}]
    flt = WINDOW + " AND is_billable AND pickup_zone_key IS NOT NULL AND dropoff_zone_key IS NOT NULL"
    assert _compile(["billable_trip_count"], od, flt).source == "LTS1_detail"
    assert _compile(["billable_trip_count"], od, flt, source="LTS6_od_flow").source == "LTS6_od_flow"


def test_non_additive_metric_reads_the_detail():
    result = _compile(["active_driver_count"], [{"via": "shift_to_date", "level": "month"}],
                      "driver_key IS NOT NULL", path=FLEET)
    assert result.source == "LTS1_detail"
    assert "count(distinct" in result.sql.lower()


def test_rate_is_rebuilt_from_summed_inputs():
    result = _compile(["occupancy_rate"], [{"via": "shift_to_driver"}], "driver_key IS NOT NULL",
                      path=FLEET)
    assert result.source.startswith("LTS")
    assert "sum(a.on_trip_hours)" in result.sql.lower() and "sum(a.online_hours)" in result.sql.lower()
    assert "a.occupancy_rate" not in result.sql


def test_detail_join_is_left_and_as_of():
    result = _compile(["trip_count"], [{"via": "trips_to_pickup_zone", "level": "borough"}],
                      source="detail")
    assert "left join core.dim_zone as d0 on f.pickup_zone_key = d0.zone_key" in result.sql


def test_extra_filter_on_an_unmapped_field_rejects_the_aggregate():
    result = _compile(["trip_count"], [{"via": "trips_to_date", "level": "month"}],
                      WINDOW + " AND pickup_zone_key IS NOT NULL AND is_fleet_attributed")
    assert result.source != "LTS2_zone_day_agg"
    assert "is_fleet_attributed" in result.rejected["LTS2_zone_day_agg"]


def test_unsupported_metric_kinds_refuse_to_compile():
    with pytest.raises(CompileError, match="time_series"):
        _compile(["billable_revenue_prior_month"])
    with pytest.raises(CompileError, match="based_on_dimensions"):
        _compile(["avg_daily_billable_revenue"])


def test_forced_source_that_cannot_answer_is_an_error():
    with pytest.raises(CompileError, match="cannot answer"):
        _compile(["trip_count"], [{"via": "trips_to_vendor"}], WINDOW, source="LTS2_zone_day_agg")


def test_compile_cli_prints_source_and_sql(tmp_path):
    query = tmp_path / "q.yaml"
    query.write_text(yaml.safe_dump({"metrics": ["trip_count"],
                                     "group_by": [{"via": "trips_to_date", "level": "month"}],
                                     "filter": WINDOW + " AND pickup_zone_key IS NOT NULL"}))
    result = RUNNER.invoke(app, ["compile", str(TRIPS), str(query)])
    assert result.exit_code == 0, result.stdout
    out = json.loads(result.stdout)
    assert out["source"] == "LTS2_zone_day_agg"
    assert "2024-01-01" not in out["sql"]  # the content filter is implied, so not repeated


def test_content_tests_are_current():
    result = RUNNER.invoke(app, ["generate-tests", "logical-model", "transformation/tests", "--check"])
    assert result.exit_code == 0, result.stdout


def test_content_tests_cover_every_aggregate_binding():
    from ossie_content import generate
    sql = generate([yaml.safe_load(TRIPS.read_text()), yaml.safe_load(FLEET.read_text())])
    assert "trips.LTS6_od_flow.billable_trip_count at " in sql  # floored: held group by group
    assert "shift.LTS2_driver_day.shift_count" in sql
    assert "occupancy_rate'" not in sql  # a rate binds no column, so it has nothing to hold


def test_compiler_joins_on_a_declared_join_expression():
    doc = yaml.safe_load(TRIPS.read_text())
    rel = next(r for r in doc["relationships"] if r["name"] == "trips_to_pickup_zone")
    payload = json.loads(rel["custom_extensions"][0]["data"])
    payload["join_expression"] = ("trips.pickup_zone_key = zone.zone_key "
                                  "AND trips.pickup_date >= zone.valid_from_date")
    rel["custom_extensions"][0]["data"] = json.dumps(payload)
    model = Model(doc, lambda t: t["source"])
    result = compile_query(model, Query(["trip_count"], [{"via": "trips_to_pickup_zone", "level": "borough"}],
                                        None, "detail"))
    assert "(f.pickup_zone_key) = (d0.zone_key) AND (f.pickup_date) >= (d0.valid_from_date)" in result.sql


def test_a_variable_in_a_query_filter_is_refused():
    with pytest.raises(CompileError, match="variables are not supported"):
        _compile(["trip_count"], filter="pickup_date >= :report_start", source="detail")
