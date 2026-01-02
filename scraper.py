import asyncio
import re
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        offres_trouvees = set()

        # --- LA CLÉ : On écoute les requêtes réseau en temps réel ---
        def handle_request(request):
            url = request.url
            if "orange-maroc.net" in url and (".svg" in url or ".png" in url):
                filename = url.split('/')[-1]
                # On cherche les prix (ex: 249dh) et les vitesses (ex: 20go)
                if "dh" in filename.lower() or "go" in filename.lower() or "mega" in filename.lower():
                    offres_trouvees.add(filename)

        page.on("request", handle_request)

        print("📡 Écoute du flux Orange (orange-maroc.net)...")
        
        try:
            # On utilise "commit" pour ne pas attendre le chargement complet
            await page.goto("https://www.orange.ma/WiFi-a-la-Maison/Fibre-d-Orange/Offres-Fibre-d-Orange", 
                            wait_until="commit", timeout=30000)
            
            # On laisse juste 10 secondes pour capturer les fichiers qui passent
            await asyncio.sleep(10)
        except Exception as e:
            print(f"⚠️ Note: Fin de l'écoute (le site est lent mais on a peut-être les données)")

        print("\n--- DONNÉES CAPTURÉES ---")
        
        prix = []
        vitesses = []

        for f in offres_trouvees:
            valeur = re.search(r'(\d+)', f)
            if valeur:
                num = valeur.group(1)
                if "dh" in f.lower():
                    prix.append(f"{num} DH")
                else:
                    vitesses.append(f"{num} Mega")

        # Affichage propre
        if not prix and not vitesses:
            print("❌ Rien n'a été capturé. Orange bloque peut-être GitHub Actions.")
        else:
            for p in sorted(list(set(prix))): print(f"✅ Prix : {p}")
            for v in sorted(list(set(vitesses))): print(f"✅ Vitesse : {v}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
