import json
import asyncio
from playwright.async_api import async_playwright

# 1. Vos 17 cibles complètes
TARGETS = {
    "Orange_Mobile": "https://boutique.orange.ma/offres-mobile",
    "Orange_Dar_Box": "https://boutique.orange.ma/dar-box",
    "Orange_Dar_Box_5G": "https://boutique.orange.ma/offres-dar-box/dar-box-5g",
    "Orange_ADSL_Ultra": "https://www.orange.ma/WiFi-a-la-Maison/ADSL-ULTRA/Offres-ADSL-ULTRA",
    "Orange_Fibre": "https://www.orange.ma/WiFi-a-la-Maison/Fibre-d-Orange/Offres-Fibre-d-Orange",
    "Yoxo_Maroc": "https://www.yoxo.ma/",
    "IAM_Mobile_Forfaits": "https://www.iam.ma/forfaits-mobile",
    "IAM_Mobile_Illimites": "https://www.iam.ma/illimites-mobile",
    "IAM_Box_El_Manzil_5G": "https://www.iam.ma/box-el-manzil-5g",
    "IAM_Box_4G": "https://www.iam.ma/box-4g",
    "IAM_ADSL": "https://www.iam.ma/offre-adsl",
    "Injoy_Maroc": "https://www.injoy.ma/injoy/home",
    "Inwi_Mobile": "https://inwi.ma/fr/particuliers/offres-mobiles/forfait-mobile",
    "Inwi_5G_iBox": "https://inwi.ma/fr/particuliers/offres-internet/wifi-a-la-maison/5g-i-box",
    "Inwi_iDar_Duo": "https://inwi.ma/fr/particuliers/offres-internet/wifi-a-la-maison/idar-duo",
    "Inwi_ADSL_Xtra": "https://inwi.ma/fr/particuliers/offres-internet/wifi-a-la-maison/adsl-xtra",
    "Inwi_Fibre": "https://inwi.ma/fr/particuliers/offres-internet/wifi-a-la-maison/fibre-optique"
}

# Mots-clés incluant les unités de vitesse pour la Fibre/ADSL
KEYWORDS = ["DH", "Dhs", "Go", "GB", "Heure", "H", "Min", "Illimit", "Méga", "Gbps", "Mbps"]

def filter_useful_info(text):
    lines = text.split('\n')
    useful = []
    for line in lines:
        line = line.strip()
        # Correction : accepte les lignes dès 2 caractères pour ne pas rater "2H", "5G", etc.
        if any(k.lower() in line.lower() for k in KEYWORDS) and 1 < len(line) < 100:
            if line not in useful:
                useful.append(line)
    return useful

async def run_scraper():
