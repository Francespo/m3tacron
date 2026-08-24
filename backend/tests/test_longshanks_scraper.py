from backend.data_structures.round_types import RoundType
from backend.scrapers.longshanks_scraper import LongshanksScraper
from backend.scripts.scrape_tournaments import _persist_list_rows
from sqlmodel import Session, create_engine


def test_parse_compact_longshanks_record_when_draw_cell_is_missing():
    assert LongshanksScraper._parse_record("2", "1", "", "6\n2/1\nSOS 1.00") == (2, 1, 0)


def test_parse_compact_longshanks_record_as_full_fallback():
    assert LongshanksScraper._parse_record("", "", "", "Player\n3/1/1") == (3, 1, 1)


def test_parse_current_longshanks_round_option():
    assert LongshanksScraper._parse_round_option("Round 3", "3") == (
        3,
        RoundType.SWISS,
    )


def test_parse_longshanks_cut_round_option_with_non_numeric_value():
    assert LongshanksScraper._parse_round_option("Top cut round 2", "cut-2") == (
        2,
        RoundType.CUT,
    )


def test_faction_only_payload_is_not_persisted_as_a_list():
    engine = create_engine("sqlite://")
    with Session(engine) as session:
        assert _persist_list_rows(session, [{"faction": "rebelalliance"}]) == {}
