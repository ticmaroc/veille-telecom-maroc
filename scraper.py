import asyncio
import json
import re
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("🔍 Connexion et extraction des données dynamiques...")
        await page.goto("https://www.orange.ma/WiFi-a-la-Maison/Fibre-d-Orange/Offres-Fibre-d-Orange", wait_until="networkidle")

        # On extrait l'objet de configuration du site (là où sont les vrais prix)
        data = await page.evaluate("() => window.drupalSettings")
        
        # On transforme tout l'objet en texte pour chercher les prix dedans
        raw_data = json.dumps(data)
        
        # On cherche tous les prix potentiels (ex: 249, 349...) associés à la fibre
        # On cherche des nombres qui reviennent souvent dans les structures de prix
        tarifs_detectes = re.findall(r'"price":"?(\d+)"?', raw_data)
        if not tarifs_detectes:
            # Si le mot "price" n'est pas utilisé, on cherche les montants classiques
            tarifs_detectes = re.findall(r'>(249|299|349|449|649|749|949)<', await page.content())

        print("\n--- RÉSULTATS DE LA VEILLE (TEMPS RÉEL) ---")
        
        # On récupère les débits affichés sur la page
        content = await page.content()
        debits = re.findall(r'(\d+)\s*(?:Méga|Go)', content)
        debits = sorted(list(set([d for d in debits if d in ['20', '50', '100', '200', '500', '1000']])), key=int)

        if tarifs_detectes:
            # On élimine les doublons et on trie
            prix_reels = sorted(list(set(tarifs_detectes)), key=int)
            for i, debit in enumerate(debits):
                # On associe le débit au prix trouvé à la même position
                p = prix_reels[i] if i < len(prix_reels) else "Non détecté"
                print(f"📡 Offre {debit}M : {p} DH")
        else:
            print("⚠️ Aucun prix dynamique trouvé. Orange a peut-être déplacé ses données.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
