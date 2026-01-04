
import os
import sys
import json
import random
import requests
from datetime import datetime, timedelta, timezone
import pathlib

# Helper to load creds similar to previous investigation
def load_creds():
    env_path = pathlib.Path(__file__).parent.parent / "function_new_recruit_tournaments" / ".env"
    print(f"Loading credentials from {env_path}")
    try:
        with open(env_path, "r") as f:
            content = f.read().strip()
            # If it is wrapped in quotes, strip them
            if content.startswith("'") and content.endswith("'"):
                content = content[1:-1]
            creds = json.loads(content)
            return creds
    except Exception as e:
        print(f"Failed to load credentials: {e}")
        sys.exit(1)

def main():
    creds = load_creds()
    user = creds.get("NR_USER", "") # Can be empty if using API_KEY
    # The API key user provided was mapped to NR_PASSWORD in our script previously
    # But let's assume standard NR_USER/NR_PASSWORD from the .env content we saw
    password = creds.get("NR_PASSWORD")
    if not password:
         password = creds.get("API_KEY") # Fallback
    
    headers = {
        "Accept": "application/json",
        "User-Agent": "ninthage-data-analytics/1.1.0",
        "NR-User": user,
        "NR-Password": password
    }

    # 1. Calculate Date Range (Last 6 Months)
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=180)
    
    print(f"Fetching tournaments from {start_date.date()} to {end_date.date()}...")

    # 2. Fetch list of tournaments
    url = "https://www.newrecruit.eu/api/tournaments"
    # Basic pagination to clear at least a page
    # status 3 = finished? or public? Investigating script used status 3.
    body = {
        "start": start_date.strftime("%Y-%m-%d"),
        "end": end_date.strftime("%Y-%m-%d"),
        "page": 1,
        "status": 3,
        "id_game_system": 6 # T9A
    }

    try:
        resp = requests.post(url, json=body, headers=headers)
        if resp.status_code != 200:
            print(f"Error fetching list: {resp.status_code} {resp.text}")
            sys.exit(1)
        
        data = resp.json()
        tournaments = data.get('tournaments', [])
        total = data.get('total', 0)
        print(f"Found {len(tournaments)} on page 1 (Total: {total}).")
        
        if not tournaments:
            print("No tournaments found.")
            sys.exit(0)

        # 3. Random Selection
        sample_size = min(100, len(tournaments))
        selected = random.sample(tournaments, sample_size)
        
        fixtures_dir = pathlib.Path(__file__).parent.parent / "tests" / "fixtures" / "new_recruit"
        fixtures_dir.mkdir(parents=True, exist_ok=True)
        print(f"Saving samples to {fixtures_dir}...")

        for t in selected:
            t_id = t.get('_id')
            t_name = t.get('name')
            print(f"Processing: {t_name} ({t_id})")
            
            # Fetch Detail (raw)
            # The 'type' field comes from here
            detail_resp = requests.post(
                 "https://www.newrecruit.eu/api/tournament",
                 json={"id": t_id},
                 headers=headers
            )
            
            if detail_resp.status_code == 200:
                with open(fixtures_dir / f"tournament_{t_id}.json", "w", encoding='utf-8') as f:
                    json.dump(detail_resp.json(), f, indent=2)
            else:
                print(f"Failed to fetch detail for {t_id}")
                continue

            # Fetch Games (raw)
            games_url = "https://www.newrecruit.eu/api/reports"
            games_body = {"id_tournament": t_id}
            
            games_resp = requests.post(games_url, json=games_body, headers=headers)
            
            if games_resp.status_code == 200:
                 with open(fixtures_dir / f"games_{t_id}.json", "w", encoding='utf-8') as f:
                    json.dump(games_resp.json(), f, indent=2)
            else:
                 print(f"Failed to fetch games for {t_id}")

    except Exception as e:
        print(f"Global Error: {e}")

if __name__ == "__main__":
    # Setup path to allow imports if needed, but pure requests is safer for a script
    # Let's try pure requests for games based on knowledge: 
    # Valid endpoint seen in other tools/docs: generic T9A usage is often /api/tournament/games or similar.
    # But wait, `investigate_nr.py` used `get_tournament_games`.
    
    # Let's look at `function_new_recruit_tournaments/main.py` or similar to see the call?
    # No, `get_tournament_games` is likely in `new_recruit_tournaments.py` or imported.
    # Step 1527 shows `new_recruit_tournaments.py`, it has `armies_from_NR_tournament` but valid `get_tournament_games` definition was NOT shown in the snippet range.
    
    # I will simple try the most common NR endpoint for games: POST /api/tournament/getResults ??
    # Actually, to avoid guessing, I will import the function.
    
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "function_new_recruit_tournaments"))
    from main import get_tournament_games # It might be in main or utility
    # investigate_nr said `from main import get_tournament_games` or similar. 
    # Wait, investigate_nr.py line 4: `from main import get_tournament_games` (implied).
    
    # Let's re-read investigate_nr.py (Step 1432).
    # `from main import get_cred_config, get_tournaments, get_tournament_games, get_tournament`
    # So `main.py` in `function_new_recruit_tournaments` has it.
    
    main()
