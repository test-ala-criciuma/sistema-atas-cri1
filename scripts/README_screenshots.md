Screenshots with Playwright

1) Instale as dependências:

   python -m pip install --upgrade pip
   pip install playwright
   python -m playwright install chromium

2) Rode o servidor Flask localmente (ex: `python app.py`) e faça login no navegador se necessário.

3) Execute o script para capturar a página desejada:

   python scripts/screenshot_playwright.py --url http://127.0.0.1:5000/discursantes_temas/polling --out screenshots

4) Os arquivos `desktop.png` e `mobile.png` serão gerados em `screenshots/`.

Observações:
- Se a página exigir autenticação, execute um login manual no navegador e use cookies de sessão, ou modifique o script para autenticar via formulário antes de tirar a captura.
- Personalize `--url` e a resolução conforme necessário.