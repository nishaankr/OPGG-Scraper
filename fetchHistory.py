import requests
import re

# ─────────────────────────────────────────────
# STEP 1 — Configuration
# ─────────────────────────────────────────────
# Change these two values to scrape any player
SUMMONER_URL = "https://op.gg/lol/summoners/euw/Afroyobro2-EUW"
REGION       = "euw"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

# ─────────────────────────────────────────────
# STEP 2 — Fetch the summoner page and get PUUID
# ─────────────────────────────────────────────
# We request the OP.GG summoner page just like a browser would.
# The PUUID is hidden inside an escaped JSON blob in a <script> tag.
# It looks like: \"puuid\":\"9Cra9iXn...PA\"

print("Fetching summoner page...")
html = requests.get(SUMMONER_URL, headers=HEADERS).text

puuid_match = re.search(r'\\"puuid\\":\\"([A-Za-z0-9_\-]{60,90})\\"', html)

if not puuid_match:
    print("❌ Could not find PUUID. Exiting.")
    exit()

puuid = puuid_match.group(1)
print(f"✅ PUUID: {puuid}\n")

# ─────────────────────────────────────────────
# STEP 3 — Call OP.GG's internal match history API
# ─────────────────────────────────────────────
# OP.GG loads match history dynamically in the browser via this internal API.
# We call it directly by passing the PUUID and region we extracted above.
# limit=20 means fetch the last 20 games. You can increase this.

API_URL = f"https://op.gg/api/v1/lol/games/{REGION}?puuid={puuid}&limit=20"

API_HEADERS = {
    "User-Agent"  : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer"     : SUMMONER_URL,   # tells the server we came from the profile page
    "Accept"      : "application/json"
}

print("Fetching match history from API...")
api_response = requests.get(API_URL, headers=API_HEADERS)
print(f"API Status: {api_response.status_code}\n")

if api_response.status_code != 200:
    print("❌ API call failed. Response:")
    print(api_response.text[:300])
    exit()

# ─────────────────────────────────────────────
# STEP 4 — Parse the JSON response
# ─────────────────────────────────────────────
# The API returns a JSON object. The match list lives under the "data" key.
# Each game object has:
#   game["myData"]["stats"] → your kills, deaths, assists, result (WIN/LOSE)
#   game["gameDuration"]    → total game time in SECONDS (e.g. 2146 = 35m 46s)

data  = api_response.json()
games = data.get("data", [])

print(f"Found {len(games)} matches\n")
print(f"{'#':<5} {'Result':<10} {'KDA':<15} {'Duration'}")
print("-" * 40)

for i, game in enumerate(games, 1):

    # "myData" contains all stats for the player we searched
    stats = game["myData"]["stats"]

    # ── Result ──────────────────────────────
    # stats["result"] is either "WIN" or "LOSE"
    result = "Victory" if stats.get("result") == "WIN" else "Defeat"

    # ── KDA ─────────────────────────────────
    # kill, death, assist are separate integer fields
    kills   = stats.get("kill",   0)
    deaths  = stats.get("death",  0)
    assists = stats.get("assist", 0)
    kda     = f"{kills}/{deaths}/{assists}"

    # ── Duration ────────────────────────────
    # gameDuration is in total seconds — convert to Xm Ys format
    total_seconds = game.get("gameDuration", 0)
    minutes = total_seconds // 60   # integer division gives whole minutes
    seconds = total_seconds % 60    # remainder gives leftover seconds
    duration = f"{minutes}m {seconds}s"

    print(f"{i:<5} {result:<10} {kda:<15} {duration}")