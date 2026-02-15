import sqlite3

def check_counts(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT id, name, player_count FROM tournament")
    tournaments = {r[0]: {'name': r[1], 'players': r[2]} for r in c.fetchall()}
    
    stats = {}
    for tid in tournaments:
        c.execute("SELECT COUNT(*) FROM playerresult WHERE tournament_id=?", (tid,))
        p_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM match WHERE tournament_id=?", (tid,))
        m_count = c.fetchone()[0]
        stats[tid] = {'tournament': tournaments[tid], 'p_real': p_count, 'm_real': m_count}
    conn.close()
    return stats

try:
    ref = check_counts("maybe_working.db")
    test = check_counts("regression_test.db")

    print(f"Reference DB has {len(ref)} tournaments.")
    print(f"Test DB has {len(test)} tournaments.")

    for tid, t_data in test.items():
        if tid not in ref:
            print(f"WARNING: Tournament {tid} exists in Test but not in Ref.")
            continue
        
        r_data = ref[tid]
        
        # Compare
        mismatches = []
        if t_data['tournament']['players'] != r_data['tournament']['players']:
             mismatches.append(f"Metadata Players: Test={t_data['tournament']['players']}, Ref={r_data['tournament']['players']}")
        if t_data['p_real'] != r_data['p_real']:
             mismatches.append(f"Real Players: Test={t_data['p_real']}, Ref={r_data['p_real']}")
        if t_data['m_real'] != r_data['m_real']:
             mismatches.append(f"Real Matches: Test={t_data['m_real']}, Ref={r_data['m_real']}")
             
        if mismatches:
            print(f"MISMATCH for Tournament {tid} ({t_data['tournament']['name']}):")
            for m in mismatches:
                print(f"  - {m}")
        else:
            print(f"MATCH for Tournament {tid} ({t_data['tournament']['name']})")
            
except Exception as e:
    print(f"Error: {e}")
