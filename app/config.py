import os


SECRET_KEY = os.environ.get('SECRET_KEY', '')

APP_DIR = os.path.dirname(os.path.abspath(__file__))
APP_NAME = 'gogcat'
PAGINATION_LENGTH = 25
SORT_PARAMS = ('title', 'price', 'discount', 'rating')

GOG_DATA_DIR = os.path.join(APP_DIR, 'gogdata')
GOG_PAGES_DIR = os.path.join(GOG_DATA_DIR, 'pages')
GOG_UPDATE_INTERVAL = 3600 # sec

GOG_API_COOKIES = {'gog_lc': 'US_USD_en-US'}
GOG_API_FILTERED_URL = 'https://www.gog.com/games/ajax/filtered'
GOG_API_HEADERS = {'accept-language': 'en-US'}
