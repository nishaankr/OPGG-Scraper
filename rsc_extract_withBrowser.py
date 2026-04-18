from playwright.sync_api import sync_playwright

SUMMONER_URL = "https://op.gg/lol/summoners/euw/G2%20Caps-1323"

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        args=["--disable-blink-features=AutomationControlled", "--start-maximized"]
    )
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080},
    )
    page = context.new_page()
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")

    print("Loading page...")
    page.goto(SUMMONER_URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(8000)

    for y in [300, 700, 1200, 1800]:
        page.evaluate(f"window.scrollTo(0, {y})")
        page.wait_for_timeout(1000)
    page.wait_for_timeout(3000)

    # ── Click "Show more" until it disappears ─────────────────────────────────
    click_count = 0
    while True:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)

        clicked = page.evaluate("""
            () => {
                const buttons = Array.from(document.querySelectorAll('button'));
                // Match EXACTLY "Show more" — case sensitive, full text match
                const btn = buttons.find(b => b.innerText.trim() === 'Show more');
                if (btn) {
                    btn.click();
                    return true;
                }
                return false;
            }
        """)

        if not clicked:
            print(f"✅ All matches loaded ({click_count} clicks total)")
            break

        click_count += 1
        print(f"  Clicked 'Show more' #{click_count}...")
        page.wait_for_timeout(3000)

        if click_count >= 30:
            print("⚠️  Safety limit reached")
            break

    # ── Extract all matches ───────────────────────────────────────────────────
    print("Extracting match data...")
    matches = page.evaluate("""
        () => {
            const results = [];
            const seen = new Set();  // deduplicate by result+kda+duration combo

            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            let node;

            while (node = walker.nextNode()) {
                const text = node.textContent.trim();
                if (text !== 'Victory' && text !== 'Defeat') continue;

                const result = text;
                let el = node.parentElement;

                for (let i = 0; i < 15; i++) {
                    if (!el) break;
                    const t = el.innerText || "";
                    const kdaMatch = t.match(/(\\d+)\\s*\\/\\s*(\\d+)\\s*\\/\\s*(\\d+)/);
                    const durMatch = t.match(/(\\d+)m\\s*(\\d+)s/);

                    if (kdaMatch && durMatch) {
                        const key = `${result}-${kdaMatch[1]}-${kdaMatch[2]}-${kdaMatch[3]}-${durMatch[1]}${durMatch[2]}`;
                        if (!seen.has(key)) {
                            seen.add(key);
                            results.push({
                                result,
                                kills:    kdaMatch[1],
                                deaths:   kdaMatch[2],
                                assists:  kdaMatch[3],
                                duration: `${durMatch[1]}m ${durMatch[2]}s`
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

# ── Print ─────────────────────────────────────────────────────────────────────
print(f"\nTotal matches scraped: {len(matches)}\n")
print(f"{'#':<5} {'Result':<10} {'Kills':<8} {'Deaths':<8} {'Assists':<10} {'Duration'}")
print("─" * 52)
for i, m in enumerate(matches, 1):
    print(f"{i:<5} {m['result']:<10} {m['kills']:<8} {m['deaths']:<8} {m['assists']:<10} {m['duration']}")