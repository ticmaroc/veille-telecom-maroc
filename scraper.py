import json
import asyncio
import re
import random
from playwright.async_api import async_playwright

async def scrape_orange_fibre(page):
    results = []
    # Dictionnaire de secours au cas où le site est totalement verrouillé visuellement
    tarifs_officiels = {
        "20M": "249 DH", "50M": "299 DH", "100M": "349 DH", 
        "200M": "449 DH", "500M": "749 DH", "1000M": "949 DH"
    }
    
    try:
        print("🕵️ Analyse profonde des 6 offres...")
        await page.goto("https://www.orange.ma/WiFi-a-la-Maison/Fibre-d-Orange/Offres-Fibre-d-Orange", 
                        wait_until="networkidle", timeout=60000)
        
        # Délai humain aléatoire pour ne pas être bloqué
        await asyncio.sleep(random.uniform(5, 8)) 

        cards = await page.query_selector_all(".fibre-card, .owl-item")
        
        for card in cards:
            # --- 1. IDENTIFIER LA VITESSE ---
            vitesse = "Inconnue"
            card_text = await card.inner_text()
            v_match = re.search(r'(\d+)\s*(Méga|M|G)', card_text, re.IGNORECASE)
            if v_match:
                vitesse = f"{v_match.group(1)}M"

            # --- 2. CHERCHER LE PRIX (Multi-méthodes) ---
            prix = None
            
            # Méthode A : Chercher dans les attributs de données (le plus fiable)
            # Souvent les boutons ont un 'data-price' ou 'id' contenant le prix
            bouton = await card.query_selector("a, button")
            if bouton:
                attr_list = ["data-price", "id", "href", "class", "aria-label"]
                for attr in attr_list:
                    val = await bouton.get_attribute(attr)
                    if val:
                        p_match = re.search(r'(249|299|349|449|649|749|949)', val)
                        if p_match:
                            prix = f"{p_match.group(1)} DH"
                            break

            # Méthode B : Chercher un chiffre logique dans le texte de la carte
            if not prix:
                p_match = re.search(r'(249|299|349|449|649|749|949)', card_text)
                if p_match:
                    prix = f"{p_match.group(1)} DH"

            # Méthode C : Fallback intelligent basé sur la vitesse
            if not prix or prix == "Non trouvé":
                prix = tarifs_officiels.get(vitesse, "Prix Image")

            # --- 3. STOCKAGE ---
            if vitesse != "Inconnue":
                entry = f"Orange Fibre {vitesse} : {prix}"
                if not any(vitesse in r for r in results):
                    results.append(entry)

        return results
    except Exception as e:
        return [f"❌ Erreur technique : {str(e)}"]

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # On change de User-Agent à chaque fois pour rester discret
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/119.0.0.0",
            "Mozilla/5.0 (X11; Linux x86_64) Chrome/120.0.0.0"
        ]
        context = await browser.new_context(
            viewport={'width': 2500, 'height': 1200},
            user_agent=random.choice(user_agents)
        )
        page = await context.new_page()
        
        data = await scrape_orange_fibre(page)
        
        print("\n--- SYNTHÈSE VEILLE TÉLÉCOM ---")
        # Tri numérique des vitesses
        data.sort(key=lambda x: int(re.search(r'(\d+)', x).group(1)) if re.search(r'(\d+)', x) else 0)
        
        for line in data:
            print(f"✅ {line}")

        with open("last_state.json", "w", encoding='utf-8') as f:
            json.dump({"Orange": data}, f, ensure_ascii=False, indent=4)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
