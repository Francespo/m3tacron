
from backend.analytics.core import aggregate_card_stats
from backend.data_structures.data_source import DataSource

def test_epic_filter():
    filters = {
        "allowed_formats": ["xwa"],
        "include_epic": True
    }
    
    # mode="pilots"
    results = aggregate_card_stats(filters, mode="pilots", data_source=DataSource.XWA)
    
    # Look for "Alderaanian Guard" (alderaanianguard)
    found = False
    for r in results:
        if r["xws"] == "alderaanianguard":
            found = True
            break
            
    if found:
        print("SUCCESS: Alderaanian Guard found with include_epic=True")
    else:
        print("FAILURE: Alderaanian Guard NOT found with include_epic=True")

if __name__ == "__main__":
    test_epic_filter()
