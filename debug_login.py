import requests
from bs4 import BeautifulSoup

LOGIN_URL = "http://localhost:5000/login"
session = requests.Session()

# Obtem a página de login
resp = session.get(LOGIN_URL)

# Salva para inspeção local
with open("login_page.html", "w", encoding="utf-8") as f:
    f.write(resp.text)

print("✅ HTML da página de login salvo como login_page.html.")
