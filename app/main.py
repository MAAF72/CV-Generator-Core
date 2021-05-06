from quart import Quart

from firebase_admin import credentials, db, initialize_app, storage
from firebase_admin.exceptions import FirebaseError

from pyppeteer import launch

from app.classes.customer import Customer
from app.classes.cv import CV
from app.classes.edukasi import Edukasi
from app.classes.bahasa import Bahasa
from app.classes.pengalaman import Pengalaman
from app.classes.penghargaan import Penghargaan
from app.classes.sosial_media import SosialMedia
from app.classes.kemampuan import Kemampuan
from app.classes.rujukan import Rujukan
from app.classes.template import Template

from pathlib import Path
from os import listdir

import json
import jinja2

cred = credentials.Certificate('app/cv-generator-e29dd-firebase-adminsdk-zvelg-ae5fe10a7a.json')
initialize_app(cred, {
    'databaseURL': 'https://cv-generator-e29dd-default-rtdb.firebaseio.com/',
    'storageBucket': 'cv-generator-e29dd.appspot.com'
})

app = Quart(__name__)

ref = db.reference('/cvs')

@app.route('/')
async def index():
    return 'OHAYOUUUU'

@app.route('/enable-cors')
async def enable_cors():
    try:
        bucket = storage.bucket()

        bucket.cors = [
            {
                'origin': ['*'],
                'method': ['GET'],
                'maxAgeSeconds': 86400
            }
        ]

        bucket.update()
    except Exception as e:
        print('Error when enabling cors', e)
        return 'ERROR'

    return 'OK'
    
@app.route('/generate/<unique_code>')
async def generate(unique_code):
    try:
        cv = ref.child(unique_code)
        py_cv = CV(cv.get())

        template_folder = f'app/templates/{py_cv.template.id}'
        html_file = f'{template_folder}/{unique_code}.html'
        pdf_file = f'temp/{unique_code}.pdf'
        
        jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(template_folder))
        
        with open(html_file, 'w+') as jinja_output:
            jinja_output.write(jinja_environment.get_template(py_cv.template.file).render(data=py_cv.customer))

        generate_result = await generate_pdf(py_cv.template.id, unique_code)
        if generate_result == 'OK':
            bucket = storage.bucket()
            blob = bucket.blob(f'cv/{unique_code}.pdf')
            blob.upload_from_filename(pdf_file)
            blob.make_public()
            
            cv.update({
                'file': blob.public_url
            })
        else:
            return 'ERROR'
    except FirebaseError as e:
        print('Error when generating cv', e)
        return 'ERROR'

    return 'OK'

async def generate_pdf(template_id, unique_code):
    abs_path = Path(__file__).parent.absolute()
    local_path = f'file://{abs_path}'
    html_file = f'{local_path}/templates/{template_id}/{unique_code}.html'
    pdf_file = f'app/temp/{unique_code}.pdf'
    try:
        print('trace 1')
        browser = await launch({
            'headless': True,
            'args': ['--no-sandbox', '--disable-setuid-sandbox'],
        })
        print('trace 2')
        page = await browser.newPage()
        print('trace 3')
        await page.setViewport({
            'height': 0,
            'width': 0, 
            'preferCSSPageSize': True,
            'deviceScaleFactor': 2
        })
        print('trace 4')
        await page.goto(html_file)
        print('trace 5')
        await page.waitFor(2000)
        print('trace 6')
        await page.pdf({
            'path': {pdf_file},
            'format': 'A4',
            'printBackground': True
        })
        print('trace 7')
        
        await browser.close()
        
        return True
    except Exception as e:
        print('error when generating pdf', e)
        
    return False