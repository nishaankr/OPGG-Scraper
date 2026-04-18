import requests
import re

opgg_url = "https://op.gg/lol/summoners/euw/Afroyobro2-EUW"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

html = requests.get(opgg_url, headers=headers).text

# Matches: \"puuid\":\"<VALUE>\"
puuid_match = re.search(r'\\"puuid\\":\\"([A-Za-z0-9_\-]{60,90})\\"', html)

if puuid_match:
    print(" PUUID found:")
    print(puuid_match.group(1))
else:
    print("PUUID Still not matched.")
    idx = html.find("puuid")
    if idx != -1:
        print(repr(html[idx:idx+120]))