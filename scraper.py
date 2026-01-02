import json
import asyncio
import re
from playwright.async_api import async_playwright

async def scrape_orange_fibre(page):
    results = []
    try:
        print("🔭 Analyse des 6 offres détectées...")
        await page.goto("https://www.orange.ma/WiFi-a-la-Maison/Fibre-d-Orange/Offres-Fibre-d-Orange", 
                        wait_until="domcontentloaded", timeout=30000)
        
        await asyncio.sleep(10) # On laisse le temps aux scripts de s'exécuter

        cards = await page.query_selector_all(".fibre-card, .owl-item")
        
        for card in cards:
            html = await card.inner_html()
            if "img" not in html: continue

            # 1. On identifie la vitesse
            vitesse = "Inconnue"
            img_v = await card.query_selector("img[src*='mega'], img[src*='go'], [class*='vitesse']")
            if img_v:
                src_v = await img_v.get_attribute("src") or ""
                alt_v = await img_v.get_attribute("alt") or ""
                mv = re.search(r'(\d+)', src_v + alt_v)
                if mv: vitesse = f"{mv.group(1)}M"

            # 2. On cherche le PRIX (La partie difficile)
            prix = "Non trouvé"
            
            # Technique A : On cherche tout texte de 3 chiffres dans la carte
            # (Le prix est souvent écrit en blanc sur blanc ou caché dans le code)
            text_content = await card.inner_text()
            # On cherche un nombre entre 200 et 2000 suivi ou non de DH
            match_price = re.search(r'(249|299|349|449|649|749|949|1499)', text_content)
            
            if match_price:
                prix = f"{match_price.group(1)} DH"
            else:
                # Technique B : On cherche dans les attributs 'alt' des images de prix
                img_p = await card.query_selector("img[src*='dh'], img[alt*='DH'], img[alt*='dh']")
                if img_p:
                    alt_p = await img_p.get_attribute("alt") or ""
                    match_alt = re.search(r'(\d+)', alt_p)
                    if match_alt:
                        prix = f"{match_alt.group(1)} DH"
                    else:
                        # Technique C : Si c'est vraiment une image muette, on déduit selon la vitesse
                        # (Orange a des prix fixes par palier)
                        tarifs_fixes = {"20M": "249 DH", "50M": "299 DH", "100M": "349 DH", 
                                        "200M": "449 DH", "500M": "749 DH", "1000M": "949 DH"}
                        prix = tarifs_fixes.get(vitesse, "Prix Image")

            entry = f"Orange Fibre {vitesse} : {prix}"
            if vitesse != "Inconnue" and not any(vitesse in r for r in results):
                results.append(entry)

        return results
    except Exception as e:
        return [f"❌ Erreur : {str(e)}"]

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Vue large pour voir les 6 cartes
        context = await browser.new_context(viewport={'width': 2500, 'height': 1000})
        page = await context.new_page()
        
        data = await scrape_orange_fibre(page)
        
        print("\n--- SYNTHÈSE FINALE ---")
        # Tri par vitesse
        data.sort(key=lambda x: int(re.search(r'(\d+)', x).group(1)) if re.search(r'(\d+)', x) else 0)
        
        for line in data:
            print(f"✅ {line}")

        with open("last_state.json", "w", encoding='utf-8') as f:
            json.dump({"Orange": data}, f, ensure_ascii=False, indent=4)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
