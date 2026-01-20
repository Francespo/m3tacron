import sqlite3

conn = sqlite3.connect('metacron.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

t_id = 29336

print(f"--- Checking Event {t_id} ---")

# 1. Check Platform/Format Case
c.execute("SELECT platform, format FROM tournament WHERE id=?", (t_id,))
row = c.fetchone()
if row:
    print(f"Platform: '{row['platform']}'")
    print(f"Format: '{row['format']}'")
else:
    print("Tournament not found")

# 2. Check Match Stats
c.execute("SELECT count(*) FROM match WHERE tournament_id=?", (t_id,))
total = c.fetchone()[0]
c.execute("SELECT count(*) FROM match WHERE tournament_id=? AND is_bye=1", (t_id,))
byes = c.fetchone()[0]
print(f"Total Matches: {total}")
print(f"Total BYEs: {byes}")

# 3. Check XWS
c.execute("SELECT count(*) FROM playerresult WHERE tournament_id=? AND list_json != '{}'", (t_id,))
xws = c.fetchone()[0]
print(f"XWS Lists: {xws}")

conn.close()
