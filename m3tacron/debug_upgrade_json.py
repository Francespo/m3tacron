import json
from pathlib import Path
from backend.utils.xwing_data.core import get_data_dir
from backend.data_structures.data_source import DataSource

data_dir = get_data_dir(DataSource.XWA)
upgrades_dir = data_dir / "upgrades"

print(f"Data Dir: {data_dir}")
print(f"Upgrades Dir: {upgrades_dir}")

found = False
for file in upgrades_dir.glob("*.json"):
    print(f"Checking {file.name}")
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list) and len(data) > 0:
                sample = data[0]
                print("Keys in first upgrade:")
                print(list(sample.keys()))
                if "image" in sample:
                    print(f"Image: {sample['image']}")
                else:
                    print("No 'image' key found.")
                    
                # Check for sides
                if "sides" in sample:
                    print("Checking sides...")
                    for side in sample["sides"]:
                        if "image" in side:
                            print(f"Side Image: {side['image']}")
                        else:
                            print("No 'image' in side.")
                found = True
                break
    except Exception as e:
        print(f"Error reading {file}: {e}")

if not found:
    print("No upgrade files found or empty.")
