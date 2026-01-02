import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("🕵️ ESPIONNAGE DES IMAGES (On affiche TOUT)...")
        
        try:
            await page.goto("https://www.orange.ma/WiFi-a-la-Maison/Fibre-d-Orange/Offres-Fibre-d-Orange", 
                            wait_until="networkidle", timeout=60000)
            
            # Petit scroll pour forcer le chargement des images du bas
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(5)
            
            # On prend TOUTES les images, sans filtre
            images = await page.eval_on_selector_all("img", "elements => elements.map(e => e.src)")
            
            print(f"\n📦 {len(images)} images trouvées au total :")
            print("-" * 50)
            
            for src in list(set(images)): # On retire les doublons
                # On affiche seulement ce qui vient d'Orange pour ne pas polluer avec les icônes Facebook etc.
                if "orange.ma" in src or "orange-maroc.net" in src:
                    print(f"🔗 {src}")

            print("-" * 50)

        except Exception as e:
            print(f"❌ Erreur : {e}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
