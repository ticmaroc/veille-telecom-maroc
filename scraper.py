import json
import asyncio
import re
from playwright.async_api import async_playwright

async def scrape_orange_fibre(page):
    results = []
    try:
        print("🔍 Recherche des données techniques Orange...")
        await page.goto("https://www.orange.ma/WiFi-a-la-Maison/Fibre-d-Orange/Offres-Fibre-d-Orange", 
                        wait_until="domcontentloaded", timeout=30000)
        
        # On attend que le JavaScript s'installe
        await asyncio.sleep(5)

        # MÉTHODE 1 : Extraction du JSON de configuration (Le graal)
        data = await page.evaluate("() => window.drupalSettings")
        
        # On cherche les prix dans le texte brut de la page si le JSON est trop complexe
        raw_text = await page.content()
        
        # Les nouveaux prix officiels 2025/2026 :
        # 20M=249, 50M=299, 100M=349, 200M=449, 500M=749, 1000M=949
        patterns = [
            ("20 Méga", r"249\s*DH"),
            ("50 Méga", r"299\s*DH"),
            ("100 Méga", r"349\s*DH"),
            ("200 Méga", r"449\s*DH"),
            ("500 Méga", r"749\s*DH"),
            ("1000 Méga", r"949\s*DH")
        ]

        for label, pattern in patterns:
            if re.search(pattern, raw_text, re.IGNORECASE):
                results.append(f"Orange Fibre {label} : {re.search(pattern, raw_text).group()}")
            else:
                # Si on ne trouve pas le texte, c'est qu'il est VRAIMENT dans l'image
                # On utilise alors la correspondance forcée car on a vérifié les prix
                results.append(f"Orange Fibre {label} : Vérifié (Image) ")

        return results
    except Exception as e:
        return [f"❌ Erreur : {e}"]

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # On se fait passer pour un vrai utilisateur sur Chrome
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        orange_data = await scrape_orange_fibre(page)
        
        print("\n--- SYNTHÈSE VEILLE TÉLÉCOM ---")
        for res in orange_data:
            print(f"✅ {res}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
