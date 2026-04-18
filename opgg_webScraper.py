from bs4 import BeautifulSoup
import requests

opgg_url = "https://op.gg/lol/summoners/euw/Afroyobro2-EUW"

response = requests.get(opgg_url)

html = response.text

print(html)