import asyncio
from playwright.async_api import async_playwright

async def debug():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_context().new_page()
        
        print("🔍 Connexion à Orange Fibre...")
        await page.goto("https://www.orange.ma/WiFi-a-la-Maison/Fibre-d-Orange/Offres-Fibre-d-Orange", wait_until="networkidle")
        await asyncio.sleep(5) # On laisse les images charger

        # On analyse chaque carte fibre une par une
        cards = await page.query_selector_all(".fibre-card")
        print(f"📦 Nombre de cartes trouvées : {len(cards)}")

        for i, card in enumerate(cards):
            print(f"\n--- CARTE N°{i+1} ---")
            # 1. On récupère le texte visible (s'il y en a)
            text = await card.inner_text()
            print(f"Texte visible : '{text.strip()}'")

            # 2. On regarde l'image (alt et src)
            img = await card.query_selector("img")
            if img:
                alt = await img.get_attribute("alt")
                src = await img.get_attribute("src")
                print(f"Image ALT : {alt}")
                print(f"Image SRC : {src}")
            
            # 3. On cherche si le prix est caché dans le code HTML de la carte
            html = await card.inner_html()
            print(f"Code HTML partiel : {html[:100]}...") 

        await browser.close()

asyncio.run(debug())
