from pyppeteer import chromium_downloader
from app.main import app

if __name__ == '__main__':
    chromium_downloader.download_chromium()
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run()