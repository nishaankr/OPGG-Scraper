from playwright.sync_api import sync_playwright

SUMMONER_URL = "https://op.gg/lol/summoners/euw/Afroyobro2-EUW"

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,           # No visible browser
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-images",           #No images
            "--disable-extensions",   #No extensions
            "--no-sandbox",
            "--disable-gpu",
        ]
    )
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080},
        #Block ads, trackers, etc
        extra_http_headers={"Accept-Language": "en-US,en;q=0.9"}
    )

    # Block images, fonts, ads
    def block_unnecessary(route):
        if route.request.resource_type in ["image", "font", "media", "stylesheet"]:
            route.abort()
        else:
            route.continue_()

    context.route("**/*", block_unnecessary)

    page = context.new_page()
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")

    print("Loading page...")
    page.goto(SUMMONER_URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(4000)               

    # Single fast scroll 
    page.evaluate("window.scrollTo(0, 1800)")
    page.wait_for_timeout(2000)                     
    # Click "Show more" loop
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
            print(" Safety limit reached")
            break

    # Extract
    print("Extracting----------------------")
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
                    const t       = el.innerText || "";
                    const kdaM    = t.match(/(\\d+)\\s*\\/\\s*(\\d+)\\s*\\/\\s*(\\d+)/);
                    const durM    = t.match(/(\\d+)m\\s*(\\d+)s/);
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

print(f"\nTotal: {len(matches)} matches\n")
print(f"{'#':<5} {'Result':<10} {'Kills':<8} {'Deaths':<8} {'Assists':<10} {'Duration'}")
print("─" * 52)
for i, m in enumerate(matches, 1):
    print(f"{i:<5} {m['result']:<10} {m['kills']:<8} {m['deaths']:<8} {m['assists']:<10} {m['duration']}")