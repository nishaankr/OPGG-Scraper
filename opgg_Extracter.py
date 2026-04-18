import re
import csv
import requests
from playwright.sync_api import sync_playwright

print("=" * 52)
print("  OP.GG Match History Scraper")
print("=" * 52)
SUMMONER_URL = input("\nPaste your OP.GG profile URL: ").strip()

if "op.gg/lol/summoners" not in SUMMONER_URL:
    print("Invalid OP.GG URL.")
    print("   Example: https://op.gg/lol/summoners/euw/Afroyobro2-EUW")
    exit()

print("\nFetching PUUID...")
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}
html = requests.get(SUMMONER_URL, headers=headers).text
puuid_match = re.search(r'\\"puuid\\":\\"([A-Za-z0-9_\-]{60,90})\\"', html)

if puuid_match:
    PUUID = puuid_match.group(1)
    print(f"PUUID: {PUUID[:20]}...{PUUID[-10:]}")
else:
    PUUID = None
    print("PUUID not found")

url_parts     = SUMMONER_URL.rstrip("/").split("/")
summoner_slug = url_parts[-1]
region        = url_parts[-2]
csv_filename  = f"{summoner_slug}_{region}_matches.csv"

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-images",
            "--disable-extensions",
            "--no-sandbox",
            "--disable-gpu",
        ]
    )
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080},
        extra_http_headers={"Accept-Language": "en-US,en;q=0.9"}
    )

    def block_unnecessary(route):
        if route.request.resource_type in ["image", "font", "media", "stylesheet"]:
            route.abort()
        else:
            route.continue_()

    context.route("**/*", block_unnecessary)

    page = context.new_page()
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")

    print(f"\nLoading page for: {summoner_slug} ({region.upper()})...")
    page.goto(SUMMONER_URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(4000)

    page.evaluate("window.scrollTo(0, 1800)")
    page.wait_for_timeout(2000)

    click_count = 0
    while True:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)

        clicked = page.evaluate("""
            () => {
                const btn = Array.from(document.querySelectorAll('button'))
                    .find(b => b.innerText.trim() === 'Show more');
                if (btn) { btn.click(); return true; }
                return false;
            }
        """)

        if not clicked:
            print(f"All matches loaded ({click_count} clicks)")
            break

        click_count += 1
        print(f"  Clicked 'Show more' #{click_count}")
        page.wait_for_timeout(1500)

        if click_count >= 30:
            print("Safety limit reached")
            break

    print("Extracting match data...")
    matches = page.evaluate("""
        () => {
            const results = [];
            const seen    = new Set();
            const walker  = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            let node;

            while (node = walker.nextNode()) {
                const text = node.textContent.trim();
                if (text !== 'Victory' && text !== 'Defeat') continue;

                let el = node.parentElement;
                for (let i = 0; i < 15; i++) {
                    if (!el) break;
                    const t    = el.innerText || "";
                    const kdaM = t.match(/(\\d+)\\s*\\/\\s*(\\d+)\\s*\\/\\s*(\\d+)/);
                    const durM = t.match(/(\\d+)m\\s*(\\d+)s/);
                    if (kdaM && durM) {
                        const key = `${text}-${kdaM[1]}-${kdaM[2]}-${kdaM[3]}-${durM[1]}${durM[2]}`;
                        if (!seen.has(key)) {
                            seen.add(key);
                            results.push({
                                result:   text,
                                kills:    kdaM[1],
                                deaths:   kdaM[2],
                                assists:  kdaM[3],
                                duration: `${durM[1]}m ${durM[2]}s`
                            });
                        }
                        break;
                    }
                    el = el.parentElement;
                }
            }
            return results;
        }
    """)

    browser.close()

print(f"\n{'=' * 52}")
print(f"  Summoner : {summoner_slug}")
print(f"  Region   : {region.upper()}")
print(f"  PUUID    : {PUUID[:20] + '...' if PUUID else 'Not found'}")
print(f"  Matches  : {len(matches)}")
print(f"{'=' * 52}\n")

print(f"{'#':<5} {'Result':<10} {'Kills':<8} {'Deaths':<8} {'Assists':<10} {'Duration'}")
print("─" * 52)
for i, m in enumerate(matches, 1):
    print(f"{i:<5} {m['result']:<10} {m['kills']:<8} {m['deaths']:<8} {m['assists']:<10} {m['duration']}")

with open(csv_filename, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["#", "result", "kills", "deaths", "assists", "duration", "summoner", "region", "puuid"])
    writer.writeheader()
    for i, m in enumerate(matches, 1):
        writer.writerow({
            "#":        i,
            "result":   m["result"],
            "kills":    m["kills"],
            "deaths":   m["deaths"],
            "assists":  m["assists"],
            "duration": m["duration"],
            "summoner": summoner_slug,
            "region":   region.upper(),
            "puuid":    PUUID or "N/A"
        })

print(f"\nSaved to: {csv_filename}")