from bs4 import BeautifulSoup
import requests
import re
import json


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

opgg_url = "https://op.gg/lol/summoners/euw/Afroyobro2-EUW"
response = requests.get(opgg_url)
html = response.text
soup = BeautifulSoup(html, "html.parser")

# All from og:description 
og_desc = soup.find("meta", property="og:description")["content"]

puuid_match = re.search(r'"puuid"[,\s:"]+([A-Za-z0-9_-]{78})', html)
if puuid_match:
    print("PUUID:", puuid_match.group(1))
    
# Extract data

rank_match   = re.search(r'(Silver|Gold|Platinum|Diamond|Emerald|Bronze|Iron|Challenger|Grandmaster|Master)\s+(\d)', og_desc, re.IGNORECASE)
lp_match     = re.search(r'(\d+)LP', og_desc)
wins_match   = re.search(r'(\d+)Win', og_desc)
losses_match = re.search(r'(\d+)Lose', og_desc)
wr_match     = re.search(r'Win rate\s+(\d+)', og_desc)

print("=== PROFILE SUMMARY ===")
print("Rank:    ", rank_match.group(1), rank_match.group(2) if rank_match else "?")
print("LP:      ", lp_match.group(1) if lp_match else "?")
print("Wins:    ", wins_match.group(1) if wins_match else "?")
print("Losses:  ", losses_match.group(1) if losses_match else "?")
print("Win Rate:", wr_match.group(1) + "%" if wr_match else "?")


#Champions
champ_pattern = re.findall(r'([A-Za-z]+) - (\d+)Win (\d+)Lose Win rate (\d+)', og_desc)
print("\nTop Champions:\n")
for name, wins, losses, wr in champ_pattern:
    print(f"  {name}: {wins}W/{losses}L - {wr}% WR")