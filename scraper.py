import asyncio
from playwright.async_api import async_playwright

async def debug():
    async with async_playwright() as p:
        # On lance le navigateur
        browser = await p.chromium.launch(headless=True)
        
        # CORRECT : On attend le contexte, PUIS on crée la page
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print("🔍 Connexion à Orange Fibre...")
        try:
            # On va sur la page
            await page.goto("https://www.orange.ma/WiFi-a-la-Maison/Fibre-d-Orange/Offres-Fibre-d-Orange", wait_until="domcontentloaded", timeout=60000)
            
            # On attend un peu que le JS s'exécute
            await asyncio.sleep(8) 

            # On cherche les cartes que tu as identifiées
            cards = await page.query_selector_all(".fibre-card")
            print(f"📦 Nombre de cartes trouvées : {len(cards)}")

            for i, card in enumerate(cards):
                print(f"\n--- CARTE N°{i+1} ---")
                
                # Récupération du texte visible
                text = await card.inner_text()
                print(f"Texte visible : '{text.strip()}'")

                # Récupération de l'image (ALT et SRC)
                img = await card.query_selector("img")
                if img:
                    alt = await img.get_attribute("alt")
                    src = await img.get_attribute("src")
                    print(f"Image ALT : {alt}")
                    print(f"Image SRC : {src}")
                
                # Extraction du HTML pour voir si le prix est caché dans un attribut
                html = await card.inner_html()
                print(f"Code HTML : {html[:150]}...") # On affiche les 150 premiers caractères

        except Exception as e:
            print(f"❌ Erreur pendant le scan : {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug())
