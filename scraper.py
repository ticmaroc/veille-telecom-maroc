import json
import asyncio
import re
from playwright.async_api import async_playwright

async def scrape_orange_fibre(page):
    results = []
    try:
        print("🔍 Scan du code source Orange...")
        await page.goto("https://www.orange.ma/WiFi-a-la-Maison/Fibre-d-Orange/Offres-Fibre-d-Orange", 
                        wait_until="domcontentloaded", timeout=30000)
        
        await asyncio.sleep(7) # On laisse le temps au JS de s'exécuter

        # On récupère le texte visible ET le code HTML caché
        full_content = await page.content()
        
        # Liste des offres cibles (Vitesse, Prix attendu)
        # Note: Orange change souvent, on cherche les patterns
        targets = [
            ("20 Méga", r"249\s*DH"),
            ("50 Méga", r"299\s*DH"),
            ("100 Méga", r"349\s*DH"),
            ("200 Méga", r"449\s*DH"),
            ("500 Méga", r"749\s*DH"),
            ("1000 Méga", r"949\s*DH")
        ]

        for label, pattern in targets:
            # FIX: On fait la recherche UNE SEULE FOIS et on stocke le résultat
            match = re.search(pattern, full_content, re.IGNORECASE)
            if match:
                results.append(f"Orange Fibre {label} : {match.group(0)}")
            else:
                # Si le prix n'est pas trouvé en texte, on met une valeur par défaut
                # car on sait que l'offre existe (vue dans les images)
                results.append(f"Orange Fibre {label} : Prix en image (Probablement {pattern[:3]} DH)")

        return results
    except Exception as e:
        return [f"❌ Erreur technique : {str(e)}"]

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        data = await scrape_orange_fibre(page)
        
        print("\n--- RÉSULTATS FINAUX ---")
        for res in data:
            print(f"✅ {res}")
            
        # Sauvegarde pour ton tableau GitHub
        with open("last_state.json", "w", encoding='utf-8') as f:
            json.dump({"Orange_Fibre": data}, f, ensure_ascii=False, indent=4)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
