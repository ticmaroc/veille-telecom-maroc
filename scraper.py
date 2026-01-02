import json
import asyncio
import re
from playwright.async_api import async_playwright

async def scrape_orange_fibre(page):
    results = []
    try:
        print("🔭 Ouverture d'une vue large pour voir les 6 offres...")
        await page.goto("https://www.orange.ma/WiFi-a-la-Maison/Fibre-d-Orange/Offres-Fibre-d-Orange", 
                        wait_until="domcontentloaded", timeout=30000)
        
        # On attend que le carrousel s'initialise
        await asyncio.sleep(10)

        # On cherche TOUTES les cartes, même celles qui essaient de se cacher
        # On utilise un sélecteur plus large pour ne rien rater
        cards = await page.query_selector_all(".fibre-card, .owl-item")
        
        print(f"📊 Cartes détectées : {len(cards)}")

        for card in cards:
            # On vérifie si la carte est vide (certaines cartes de carrousel sont des clones vides)
            html = await card.inner_html()
            if "img" not in html:
                continue

            # --- Extraction Vitesse ---
            vitesse = "Inconnue"
            img_v = await card.query_selector("img[src*='mega'], img[src*='go'], img[alt*='Méga']")
            if img_v:
                src_v = await img_v.get_attribute("src")
                mv = re.search(r'(\d+)', src_v)
                if mv: vitesse = f"{mv.group(1)}M"

            # --- Extraction Prix ---
            prix = "Prix Image"
            img_p = await card.query_selector("img[src*='dh']")
            if img_p:
                src_p = await img_p.get_attribute("src")
                mp = re.search(r'(\d+)', src_p)
                if mp: prix = f"{mp.group(1)} DH"
            
            # Nettoyage des doublons : on n'ajoute que si la vitesse n'est pas déjà là
            entry = f"Orange Fibre {vitesse} : {prix}"
            if vitesse != "Inconnue" and entry not in results:
                results.append(entry)

        # Tri final par vitesse pour avoir 20, 50, 100, 200, 500, 1000
        return results
    except Exception as e:
        return [f"❌ Erreur : {str(e)}"]

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # LA CLÉ : Une fenêtre de 3000px de large pour forcer l'affichage de tout le carrousel
        context = await browser.new_context(viewport={'width': 3000, 'height': 1000})
        page = await context.new_page()
        
        data = await scrape_orange_fibre(page)
        
        print("\n--- SYNTHÈSE COMPLÈTE (6 OFFRES) ---")
        # On trie les résultats par le nombre de Méga pour la propreté
        data.sort(key=lambda x: int(re.search(r'(\d+)', x).group(1)) if re.search(r'(\d+)', x) else 0)
        
        for line in data:
            print(f"✅ {line}")

        with open("last_state.json", "w", encoding='utf-8') as f:
            json.dump({"Orange": data}, f, ensure_ascii=False, indent=4)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
