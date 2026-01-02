import asyncio
import re
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # On va stocker les résultats ici
        resultats = {}

        print("🚀 Lancement de l'extraction (Mode Ultra-Rapide)...")
        
        try:
            # On n'attend PAS que le réseau soit calme (trop long/bloqué)
            # On attend juste que le code de base soit là
            await page.goto("https://www.orange.ma/WiFi-a-la-Maison/Fibre-d-Orange/Offres-Fibre-d-Orange", 
                            wait_until="commit", timeout=90000)
            
            # On laisse 10 secondes au carrousel pour injecter ses images dans le code
            await asyncio.sleep(10)

            # On récupère TOUTES les images du domaine que TU as trouvé
            images = await page.query_selector_all("img")
            urls_a_scanner = []
            
            for img in images:
                src = await img.get_attribute("src") or ""
                if "orange-maroc.net" in src and ".svg" in src:
                    urls_a_scanner.append(src)

            print(f"📦 {len(urls_a_scanner)} composants détectés. Analyse du contenu...")

            for url in set(urls_a_scanner):
                # On télécharge le contenu du SVG (c'est du texte XML)
                response = await page.request.get(url)
                content = await response.text()
                
                # On cherche un nombre de 2 ou 3 chiffres dans le fichier SVG
                # C'est là que se cache le prix ou la vitesse
                chiffres = re.findall(r'>(\d+)<', content)
                if not chiffres:
                    # Parfois le texte est dans un attribut et pas entre balises
                    chiffres = re.findall(r'(\d+)', content)
                
                filename = url.split('/')[-1]
                if chiffres:
                    valeur = chiffres[0]
                    if "dh" in filename.lower() or int(valeur) > 100:
                        print(f"💰 Prix trouvé dans {filename} : {valeur} DH")
                    elif "go" in filename.lower() or "mega" in filename.lower():
                        print(f"🚀 Vitesse trouvée dans {filename} : {valeur} Mega")

        except Exception as e:
            print(f"❌ Erreur : {e}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
