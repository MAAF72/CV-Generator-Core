from quart import Quart
from quart_cors import cors

from firebase_admin import credentials, db, initialize_app, storage
from firebase_admin.exceptions import FirebaseError

from pyppeteer import launch

from pathlib import Path
from os import path, makedirs

from app.classes.cv import CV

import jinja2

cred = credentials.Certificate('app/cv-generator-e29dd-firebase-adminsdk-zvelg-ae5fe10a7a.json')
initialize_app(cred, {
    'databaseURL': 'https://cv-generator-e29dd-default-rtdb.firebaseio.com/',
    'storageBucket': 'cv-generator-e29dd.appspot.com'
})

app = Quart(__name__)
app = cors(app, allow_origin='*')

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
        pdf_file = f'app/temp/{unique_code}.pdf'
        
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
            print('GENERATE RESULT ERROR')
            return 'ERROR'
    except FirebaseError as e:
        print('Firebase error when generating cv', e)
        return 'ERROR'
    except Exception as e:
        print('Firebase error when generating cv', e)
        return 'ERROR'
    else:
        return 'OK'

    

async def generate_pdf(template_id, unique_code):
    abs_path = Path(__file__).parent.absolute()
    local_path = f'file://{abs_path}'
    html_file = f'{local_path}/templates/{template_id}/{unique_code}.html'
    pdf_file = f'app/temp/{unique_code}.pdf'

    if not path.exists('app/temp/'):
        makedirs('app/temp/')

    try:
        browser = await launch({
            'headless': True,
            'args': ['--no-sandbox', '--disable-setuid-sandbox'],
        })
        page = await browser.newPage()
        await page.setViewport({
            'height': 0,
            'width': 0, 
            #'preferCSSPageSize': True,
            'deviceScaleFactor': 2
        })
        await page.goto(html_file)
        await page.waitFor(3000)
        await page.pdf({
            'path': pdf_file,
            'format': 'A4',
            'printBackground': True
        })
        
        await browser.close()
        
    except Exception as e:
        print('error when generating pdf', e)
        return 'ERROR'
    else:
        return 'OK'