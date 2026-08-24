import urllib.request
import os

font_url = 'https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Bold.ttf'
if not os.path.exists('Montserrat-Bold.ttf'):
    urllib.request.urlretrieve(font_url, 'Montserrat-Bold.ttf')
    print("Font downloaded.")
else:
    print("Font already exists.")
