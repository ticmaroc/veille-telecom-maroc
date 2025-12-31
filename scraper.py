import json
import asyncio
import re
import aiohttp
from playwright.async_api import async_playwright

async def get_price_from_svg(url):
    """Télécharge le SVG et cherche un prix dedans"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    content = await response.text()
                    # On cherche un nombre suivi de DH ou dh dans le code de l'image
                    match = re.search(r'(\d+)\s*(?:DH|dh)', content)
                    if match:
                        return f"{match.group(1)} DH"
    except:
        pass
    return "Prix inconnu"

async def scrape_orange_fibre(context):
    page = await context.new_page()
    results = []
    try:
        await page.goto("https://www.orange.ma/WiFi-a-la-Maison/Fibre-d-Orange/Offres-Fibre-d-Orange", wait_until="networkidle")
        cards = await page.query_selector_all(".fibre-card")
        
        for card in cards:
            img = await card.query_selector("img")
            if img:
                alt = await img.get_attribute("alt")   # "20 Méga"
                src = await img.get_attribute("src")   # "https://.../20go.svg"
                
                # On va lire l'intérieur de l'image !
                price = await get_price_from_svg(src)
                results.append(f"Orange Fibre {alt} : {price}")
        
        await page.close()
        return results
    except:
        await page.close()
        return ["❌ Erreur Orange Fibre"]

# ... (Reste du script pour IAM, Inwi, etc.)
