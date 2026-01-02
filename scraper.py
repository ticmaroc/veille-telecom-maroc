import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # On va stocker TOUTES les URLs de ce domaine
        urls_capturees = []

        def handle_request(request):
            url = request.url
            if "orange-maroc.net" in url:
                urls_capturees.append(url)

        page.on("request", handle_request)

        print("📡 Scan complet du domaine orange-maroc.net...")
        try:
            await page.goto("https://www.orange.ma/WiFi-a-la-Maison/Fibre-d-Orange/Offres-Fibre-d-Orange", 
                            wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(10) # On laisse tout charger
        except:
            pass

        print("\n--- LISTE DE TOUS LES COMPOSANTS TROUVÉS ---")
        # On affiche tout pour ne rien rater
        for url in sorted(list(set(urls_capturees))):
            filename = url.split('/')[-1]
            print(f"🔗 Fichier : {filename}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
