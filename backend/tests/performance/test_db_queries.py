import os
import pytest
import time
from datetime import datetime, timedelta
from sqlmodel import Session, select, func

from backend.database import engine
from backend.models import Tournament, PlayerResult, Match
from backend.analytics.factions import get_meta_snapshot
from backend.data_structures.data_source import DataSource


pytestmark = pytest.mark.performance


@pytest.fixture(scope="module")
def db_session():
    with Session(engine) as session:
        yield session


@pytest.fixture(scope="module")
def has_data(db_session):
    count = db_session.exec(select(func.count(Tournament.id))).one()
    return count > 0


@pytest.mark.skipif(
    not os.getenv("DATABASE_URL", "").startswith("postgresql"),
    reason="Performance benchmarks require PostgreSQL"
)
class TestDatabaseQueries:

    @pytest.mark.performance
    def test_tournament_count(self, benchmark, db_session, has_data):
        if not has_data:
            pytest.skip("No tournament data")

        def query():
            return db_session.exec(select(func.count(Tournament.id))).one()

        result = benchmark(query)
        assert result >= 0

    @pytest.mark.performance
    def test_recent_tournaments(self, benchmark, db_session, has_data):
        if not has_data:
            pytest.skip("No tournament data")

        start_date = datetime.now() - timedelta(days=90)

        def query():
            return db_session.exec(
                select(Tournament).where(Tournament.date >= start_date).limit(100)
            ).all()

        result = benchmark(query)
        assert isinstance(result, list)

    @pytest.mark.performance
    def test_player_results_with_tournament(self, benchmark, db_session, has_data):
        if not has_data:
            pytest.skip("No tournament data")

        def query():
            return db_session.exec(
                select(PlayerResult).join(Tournament).limit(100)
            ).all()

        result = benchmark(query)
        assert isinstance(result, list)

    @pytest.mark.performance
    def test_match_count(self, benchmark, db_session, has_data):
        if not has_data:
            pytest.skip("No tournament data")

        def query():
            return db_session.exec(select(func.count(Match.id))).one()

        result = benchmark(query)
        assert result >= 0

    @pytest.mark.performance
    def test_tournament_with_results(self, benchmark, db_session, has_data):
        if not has_data:
            pytest.skip("No tournament data")

        def query():
            tournaments = db_session.exec(
                select(Tournament).limit(10)
            ).all()
            for t in tournaments:
                db_session.exec(
                    select(PlayerResult).where(PlayerResult.tournament_id == t.id)
                ).all()
            return tournaments

        result = benchmark(query)
        assert isinstance(result, list)

    @pytest.mark.performance
    def test_faction_distribution(self, benchmark, db_session, has_data):
        if not has_data:
            pytest.skip("No tournament data")

        def query():
            return db_session.exec(
                select(PlayerResult.list_json).limit(500)
            ).all()

        result = benchmark(query)
        assert isinstance(result, list)

    @pytest.mark.performance
    def test_meta_snapshot_query(self, benchmark, has_data):
        if not has_data:
            pytest.skip("No tournament data")

        def query():
            return get_meta_snapshot(DataSource.XWA, allowed_formats=None)

        result = benchmark(query)
        assert "factions" in result

    @pytest.mark.performance
    def test_tournament_date_range(self, benchmark, db_session, has_data):
        if not has_data:
            pytest.skip("No tournament data")

        def query():
            return db_session.exec(
                select(func.min(Tournament.date), func.max(Tournament.date))
            ).one()

        result = benchmark(query)
        assert result is not None

    @pytest.mark.performance
    def test_player_result_aggregation(self, benchmark, db_session, has_data):
        if not has_data:
            pytest.skip("No tournament data")

        def query():
            return db_session.exec(
                select(
                    func.count(PlayerResult.id),
                    func.avg(PlayerResult.swiss_wins)
                ).join(Tournament)
            ).one()

        result = benchmark(query)
        assert result is not None

    @pytest.mark.performance
    def test_match_by_round(self, benchmark, db_session, has_data):
        if not has_data:
            pytest.skip("No tournament data")

        def query():
            return db_session.exec(
                select(Match).where(Match.round_number <= 3).limit(100)
            ).all()

        result = benchmark(query)
        assert isinstance(result, list)
