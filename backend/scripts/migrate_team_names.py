"""
Backfill `team_id` from existing `playerstanding.team_name` values.

Safe steps:
- For each tournament, find distinct non-null team_name values in `playerstanding`.
- Create a `teamstanding` row for each team name (if not exists) linked to that tournament.
- Update `playerstanding.team_id` to point to the created team id where team_name matches.

Note: This script does NOT drop the `team_name` column. Dropping columns in SQLite is destructive and should be done with a proper migration tool.
"""
from sqlmodel import Session, select
from ..database import engine
from ..models import Tournament, TeamStanding


def main():
    with Session(engine) as session:
        # Get tournaments with players
        tournaments = session.exec(select(Tournament)).all()
        for t in tournaments:
            # Raw SQL to fetch distinct team_name values directly from DB
            res = session.exec(
                "SELECT DISTINCT team_name FROM playerstanding WHERE tournament_id = :tid AND team_name IS NOT NULL AND team_name != ''",
                params={"tid": t.id},
            ).all()
            team_names = [r[0] if isinstance(r, tuple) else r for r in res]
            if not team_names:
                continue

            print(f"Tournament {t.id} '{t.name}': found teams: {team_names}")

            # Create TeamStanding rows for each team name if missing
            existing = {ts.team_name.lower(): ts for ts in session.exec(
                select(TeamStanding).where(TeamStanding.tournament_id == t.id)).all()}
            created = {}
            for name in team_names:
                key = name.lower().strip()
                if key in existing:
                    created[key] = existing[key].id
                    continue
                ts = TeamStanding(tournament_id=t.id, team_name=name)
                session.add(ts)
                session.flush()
                created[key] = ts.id
                print(f"  Created TeamStanding id={ts.id} name={name}")

            # Update playerstanding.team_id via raw SQL
            for name, tid in created.items():
                session.exec(
                    "UPDATE playerstanding SET team_id = :tid WHERE tournament_id = :tournament_id AND lower(team_name) = :tname",
                    params={"tid": tid, "tournament_id": t.id, "tname": name},
                )
            session.commit()
            print(f"  Backfilled player.team_id for tournament {t.id}")


if __name__ == '__main__':
    main()
