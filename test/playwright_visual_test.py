"""Playwright visual smoke test:
- Captura screenshots do login e da página de formulário sacramental em desktop e mobile.
- Salva imagens em test/artifacts/

Uso: python test/playwright_visual_test.py
"""
import os
from datetime import datetime, timedelta

ARTIFACTS_DIR = os.path.join('test', 'artifacts')
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

URL_BASE = os.environ.get('APP_URL', 'http://localhost:5000')
USERNAME = os.environ.get('TEST_USER', 'Criciuma_1')
PASSWORD = os.environ.get('TEST_PASS', 'Criciuma1.33@2033')

try:
    from playwright.sync_api import sync_playwright
except Exception as e:
    print('ImportError: Playwright is not installed. Run `pip install playwright` and `playwright install`.')
    raise

# compute next sunday
today = datetime.now().date()
days_to_sunday = (6 - today.weekday()) % 7
next_sunday = today if days_to_sunday == 0 else today + timedelta(days=days_to_sunday)
data_str = next_sunday.strftime('%Y-%m-%d')

with sync_playwright() as p:
    # Desktop
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width':1280, 'height':800})
    page = context.new_page()
    page.goto(URL_BASE + '/', wait_until='domcontentloaded')
    page.wait_for_selector('form')
    page.screenshot(path=os.path.join(ARTIFACTS_DIR, 'login-desktop.png'), full_page=False)

    # focus password and take screenshot showing eye alignment
    if page.query_selector('#password'):
        page.focus('#password')
        page.screenshot(path=os.path.join(ARTIFACTS_DIR, 'login-password-focus-desktop.png'), full_page=False)

    # perform login
    page.fill('input[name="username"]', USERNAME)
    page.fill('input[name="password"]', PASSWORD)
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')
    page.screenshot(path=os.path.join(ARTIFACTS_DIR, 'after-login-desktop.png'), full_page=False)

    # navigate to sacramental form
    page.goto(f"{URL_BASE}/ata/form?tipo=sacramental&data={data_str}")
    try:
        page.wait_for_selector('h1', timeout=10000)
    except Exception:
        # proceed even if the selector didn't become visible in time
        pass
    page.screenshot(path=os.path.join(ARTIFACTS_DIR, 'sacramental-desktop.png'), full_page=True)

    context.close()
    browser.close()

    # Mobile (iPhone 12)
    browser = p.chromium.launch(headless=True)
    # Use the devices list available on the Playwright instance for compatibility
    iphone = p.devices.get('iPhone 12')
    context = browser.new_context(**iphone)
    page = context.new_page()
    page.goto(URL_BASE + '/', wait_until='networkidle')
    page.wait_for_selector('form')
    page.screenshot(path=os.path.join(ARTIFACTS_DIR, 'login-mobile.png'), full_page=False)

    # show password field focus
    if page.query_selector('#password'):
        page.focus('#password')
        page.screenshot(path=os.path.join(ARTIFACTS_DIR, 'login-password-focus-mobile.png'))

    # login
    page.fill('input[name="username"]', USERNAME)
    page.fill('input[name="password"]', PASSWORD)
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')
    page.screenshot(path=os.path.join(ARTIFACTS_DIR, 'after-login-mobile.png'))

    page.goto(f"{URL_BASE}/ata/form?tipo=sacramental&data={data_str}")
    try:
        page.wait_for_selector('h1', timeout=10000)
    except Exception:
        pass
    page.screenshot(path=os.path.join(ARTIFACTS_DIR, 'sacramental-mobile.png'), full_page=True)

    context.close()
    browser.close()

print('Screenshots saved to', ARTIFACTS_DIR)
