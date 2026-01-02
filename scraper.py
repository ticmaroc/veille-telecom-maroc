import asyncio
import json
import re
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("🍊 Scan Orange (via les noms de fichiers images)...")
        
        # On va sur la page
        try:
            await page.goto("https://www.orange.ma/WiFi-a-la-Maison/Fibre-d-Orange/Offres-Fibre-d-Orange", 
                            wait_until="domcontentloaded", timeout=60000)
            
            # On laisse le temps au carrousel de charger les images
            await asyncio.sleep(5)
            
            # On récupère TOUTES les sources d'images de la page
            images_src = await page.eval_on_selector_all("img", "elements => elements.map(e => e.src)")
            
            offres_detectees = []
            
            # On nettoie les doublons pour ne pas traiter 50 fois la même image
            images_uniques = list(set(images_src))
            
            # LISTE DE RÉFÉRENCE (Mapping)
            # Puisqu'on ne peut pas lier mathématiquement l'image A à l'image B sans IA,
            # on détecte simplement QUELS PRIX sont présents sur la page.
            # Si le fichier "249dh.svg" existe, c'est que l'offre à 249 DH est active.
            
            for src in images_uniques:
                if "orange-maroc.net" in src and ".svg" in src:
                    filename = src.split('/')[-1]
                    
                    # On cherche un motif type "249dh.svg"
                    match_prix = re.search(r'(\d+)dh', filename.lower())
                    
                    if match_prix:
                        prix = int(match_prix.group(1))
                        
                        # On devine la vitesse associée basée sur le prix standard Maroc
                        # (C'est la seule façon de reconstruire le tableau sans OCR)
                        vitesse = "Inconnue"
                        if prix == 249: vitesse = "20M"
                        elif prix == 299: vitesse = "50M"
                        elif prix == 349: vitesse = "100M"
                        elif prix == 449: vitesse = "200M"
                        elif prix == 749: vitesse = "500M"
                        elif prix == 949: vitesse = "1000M"
                        
                        offres_detectees.append({
                            "offre": f"Fibre {vitesse}",
                            "vitesse": vitesse,
                            "prix": prix,
                            "source_image": filename
                        })

            # Tri des offres par prix croissant
            offres_detectees.sort(key=lambda x: x['prix'])

            # Création du JSON final
            resultat_final = {
                "operateur": "Orange Maroc",
                "type": "Fibre Optique",
                "date_scan": "Automatique",
                "offres": offres_detectees
            }

            # Affichage console pour vérification immédiate
            print("\n✅ RÉSULTATS ORANGE :")
            for o in offres_detectees:
                print(f"🔹 {o['offre']} : {o['prix']} DH (Image détectée: {o['source_image']})")
            
            # Sauvegarde JSON
            with open("orange_data.json", "w", encoding="utf-8") as f:
                json.dump(resultat_final, f, indent=4, ensure_ascii=False)
                
        except Exception as e:
            print(f"❌ Erreur critique : {e}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
