#!/usr/bin/env python3
"""Take desktop and mobile screenshots of a page using Playwright.

Usage:
  pip install playwright
  python -m playwright install chromium
  python scripts/screenshot_playwright.py --url http://127.0.0.1:5000/discursantes_temas/polling --out screenshots

Notes:
- Ensure your Flask server is running locally and you're logged in if the page requires auth.
- You can customize viewport sizes or add extra pages to capture.
"""
import os
import argparse
from playwright.sync_api import sync_playwright


def capture(url, outdir):
    os.makedirs(outdir, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        # Desktop
        page = browser.new_page(viewport={'width': 1280, 'height': 800})
        page.goto(url, wait_until='networkidle')
        page.screenshot(path=os.path.join(outdir, 'desktop.png'), full_page=True)
        print('Saved', os.path.join(outdir, 'desktop.png'))

        # Mobile (iPhone 12 emulation)
        iphone = p.devices.get('iPhone 12')
        mobile_page = browser.new_page(**iphone)
        mobile_page.goto(url, wait_until='networkidle')
        mobile_page.screenshot(path=os.path.join(outdir, 'mobile.png'), full_page=True)
        print('Saved', os.path.join(outdir, 'mobile.png'))

        browser.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True, help='Full URL to capture (e.g. http://127.0.0.1:5000/... )')
    parser.add_argument('--out', default='screenshots', help='Output directory')
    args = parser.parse_args()
    capture(args.url, args.out)
