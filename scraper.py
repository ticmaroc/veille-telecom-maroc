import json
import asyncio
import re
from playwright.async_api import async_playwright

async def scrape_orange_fibre(page):
    results = []
    try:
        print("🚀 Chargement d'Orange Fibre...")
        await page.goto("https://www.orange.ma/WiFi-a-la-Maison/Fibre-d-Orange/Offres-Fibre-d-Orange", 
                        wait_until="networkidle", timeout=60000)
        
        # --- ACTION : On simule un défilement pour charger toutes les cartes ---
        await page.mouse.wheel(0, 500)
        await asyncio.sleep(2)
        
        # On essaie de cliquer sur les flèches du carrousel pour "réveiller" les prix
        try:
            next_buttons = await page.query_selector_all(".owl-next, .next-button, [class*='next']")
            for btn in next_buttons:
                await btn.click()
                await asyncio.sleep(1)
        except:
            pass

        # On récupère le contenu après avoir "bougé" la page
        full_content = await page.content()
        
        # Regex plus flexible pour attraper "299 Dh", "299DH", "299   DH", etc.
        targets = [
            ("20 Méga", r"249\s*D[Hh]"),
            ("50 Méga", r"299\s*D[Hh]"),
            ("100 Méga", r"349\s*D[Hh]"),
            ("200 Méga", r"449\s*D[Hh]"),
            ("500 Méga", r"749\s*D[Hh]"),
            ("1000 Méga", r"949\s*D[Hh]")
        ]

        for label, pattern in targets:
            match = re.search(pattern, full_content, re.IGNORECASE)
            if match:
                # On nettoie le texte trouvé pour qu'il soit propre
                clean_price = re.sub(r'\s+', ' ', match.group(0)).upper()
                results.append(f"Orange Fibre {label} : {clean_price}")
            else:
                results.append(f"Orange Fibre {label} : Non détecté (Vérifier manuellement)")

        return results
    except Exception as e:
        return [f"❌ Erreur : {str(e)}"]

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        orange_data = await scrape_orange_fibre(page)
        
        print("\n--- RÉSULTATS DE LA VEILLE ---")
        for res in orange_data:
            print(f"✅ {res}")
            
        # Sauvegarde JSON
        with open("last_state.json", "w", encoding='utf-8') as f:
            json.dump({"Orange": orange_data}, f, ensure_ascii=False, indent=4)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
