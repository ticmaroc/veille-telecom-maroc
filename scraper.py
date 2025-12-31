import json
import asyncio
import re
from playwright.async_api import async_playwright

async def scrape_orange_fibre(context):
    page = await context.new_page()
    results = []
    try:
        print("🌐 Scan profond d'Orange Fibre...")
        await page.goto("https://www.orange.ma/WiFi-a-la-Maison/Fibre-d-Orange/Offres-Fibre-d-Orange", wait_until="networkidle", timeout=60000)
        
        # 1. On récupère TOUT le contenu de la page (même le code caché)
        content = await page.content()
        
        # 2. On cherche les prix "logiques" (entre 199 et 2000 DH)
        # On cherche un nombre de 3 ou 4 chiffres suivi de DH
        prices = re.findall(r'([2-9]\d{2,3})\s*(?:DH|dh)', content)
        # On enlève les doublons et on trie
        prices = sorted(list(set(prices)))

        # 3. On récupère les vitesses (20, 50, 100...)
        speeds = ["20 Méga", "50 Méga", "100 Méga", "200 Méga", "500 Méga", "1000 Méga"]

        # 4. On associe les deux (Heuristique)
        # Généralement : 20M=249, 50M=349, 100M=449...
        for i in range(len(prices)):
            if i < len(speeds):
                results.append(f"Orange Fibre {speeds[i]} : {prices[i]} DH")
        
        if not results:
            # Si le scan JSON échoue, on tente de lire les balises "data"
            results = await page.evaluate("""() => {
                let items = [];
                document.querySelectorAll('[data-price]').forEach(el => {
                    items.push(el.getAttribute('data-price') + " DH");
                });
                return items;
            }""")

        await page.close()
        return results if results else ["⚠️ Prix introuvables (Protections Orange)"]
    except Exception as e:
        await page.close()
        return [f"❌ Erreur : {str(e)}"]

async def run_scraper():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        orange_fibre = await scrape_orange_fibre(context)
        
        # Affichage propre dans les logs
        print("\n--- RÉSULTATS ORANGE FIBRE ---")
        for res in orange_fibre:
            print(f"✅ {res}")

        # Sauvegarde
        output = {"Orange_Fibre": orange_fibre}
        with open("last_state.json", "w", encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=4)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
