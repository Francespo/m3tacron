import sqlite3
import json

conn = sqlite3.connect('metacron.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

def print_section(title):
    print(f"\n{'='*40}")
    print(title)
    print(f"{'='*40}")

try:
    # 1. Check Tournament Formats/Platforms
    print_section("TOURNAMENTS (Check casing)")
    cursor.execute("SELECT id, name, platform, format FROM tournament")
    for row in cursor.fetchall():
        print(f"ID: {row['id']}, Name: {row['name']}, Platform: {row['platform']}, Format: {row['format']}")

    # 2. Check Players (Points & Lists)
    print_section("PLAYERS (Check XWS & Points)")
    cursor.execute("SELECT id, player_name, points_at_event, list_json FROM playerresult WHERE tournament_id = 1 LIMIT 5")
    for row in cursor.fetchall():
        list_brief = "len=" + str(len(row['list_json'])) if row['list_json'] else "None"
        print(f"Name: {row['player_name']}, Points: {row['points_at_event']}, List: {list_brief}...")
        if row['list_json'] and row['list_json'] != '{}':
             print(f"  Sample JSON: {row['list_json'][:50]}...")

    # Check if list_json is actually populated
    cursor.execute("SELECT count(*) FROM playerresult WHERE list_json != '{}' AND list_json IS NOT NULL")
    non_empty_lists = cursor.fetchone()[0]
    print(f"\nTotal non-empty lists in DB: {non_empty_lists}")

    # 3. Check Matches (Check BYEs)
    print_section("MATCHES (Check BYEs)")
    cursor.execute("SELECT round_number, player1_name, player2_name, is_bye, winner_name FROM match WHERE tournament_id = 1 LIMIT 20")
    for row in cursor.fetchall():
        print(f"R{row['round_number']}: {row['player1_name']} vs {row['player2_name']} (Bye: {row['is_bye']}) -> Winner: {row['winner_name']}")
    
    # Count byes
    cursor.execute("SELECT count(*) FROM match WHERE tournament_id=1")
    total_matches = cursor.fetchone()[0]
    cursor.execute("SELECT count(*) FROM match WHERE tournament_id=1 AND is_bye=1")
    bye_matches = cursor.fetchone()[0]
    print(f"\nTotal Matches: {total_matches}")
    print(f"Total BYEs: {bye_matches}")

finally:
    conn.close()
