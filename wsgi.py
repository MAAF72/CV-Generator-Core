from pyppeteer import chromium_downloader
from app.main import app

if __name__ == '__main__':
    print('Downloading chromium for pyppeteer')
    chromium_downloader.download_chromium()
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(host='0.0.0.0', debug=True)