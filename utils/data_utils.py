import csv
from models.ev_scooter import EVScooter

def is_duplicate_ev(name: str, seen_names: set) -> bool:
    return name in seen_names

def is_complete_ev(ev: dict, required_keys: list) -> bool:
    return all(key in ev for key in required_keys)

def save_ev_to_csv(evs: list, filename: str):
    if not evs:
        print("No EVs to save.")
        return

    fieldnames = EVScooter.model_fields.keys()

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(evs)

    print(f"Saved {len(evs)} EV scooters to '{filename}'.")
