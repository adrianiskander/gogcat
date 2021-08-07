import json, os, random, time

import requests


class GOGAPI:
    """GOG.com API wrapper."""
    def __init__(self, config):
        self.config = config

    def create_data_dirs(self):
        """Create data directories."""
        for path in (self.config.GOG_DATA_DIR, self.config.GOG_PAGES_DIR):
            if not os.path.exists(path):
                os.mkdir(path)

    def create_data_meta(self):
        """Create data meta file."""
        page_num = 1
        page = self.get_remote_page(page_num)
        if not page:
            return None
        meta = self.get_page_meta(page)
        page = self.parse_page(page)
        meta_path = os.path.join(self.config.GOG_DATA_DIR, 'meta.json')
        page_path = self.create_page_path(page_num)
        self.save_json(meta_path, meta)
        self.save_json(page_path, page)
        return meta

    def create_meta_path(self):
        path = os.path.join(self.config.GOG_DATA_DIR, 'meta.json')
        return path

    def create_page_path(self, page_num):
        page_path = os.path.join(
            self.config.GOG_PAGES_DIR, f'{page_num}.json'
        )
        return page_path

    def create_page_url(self, page_num):
        page_url = f'{self.config.GOG_API_FILTERED_URL}?page={page_num}'
        return page_url

    def create_products_path(self):
        path = os.path.join(self.config.GOG_DATA_DIR, 'products.json')
        return path

    def get_curr_time(self):
        """Get current timestamp (in seconds)."""
        curr_time = int(time.time())
        return curr_time

    def get_meta(self):
        """Get meta data or create if doesn't exists."""
        path = self.create_meta_path()
        meta = self.load_json(path)
        return meta if meta else None

    def get_page(self, page_num):
        """Get local or remote page."""
        curr_time = self.get_curr_time()
        page_path = self.create_page_path(page_num)
        page = self.load_json(page_path)
        update_interval = self.config.GOG_UPDATE_INTERVAL

        if not page or page['time'] <= curr_time - update_interval:
            page = self.get_remote_page(page_num)
            if not page or len(page['products']) < 1:
                return None
            page = self.parse_page(page)
            self.save_json(page_path, page)

        return page

    def get_page_meta(self, page):
        meta = {
            'time': self.get_curr_time(),
            'totalGames': int(page['totalGamesFound']),
            'totalMovies': int(page['totalMoviesFound']),
            'totalPages': int(page['totalPages']),
            'totalProducts': int(page['totalResults']),
        }
        return meta

    def get_product_by_slug(self, slug):
        path = os.path.join(self.config.GOG_DATA_DIR, 'products.json')
        products = self.load_json(path)
        if products:
            for product in products:
                if product['slug'] == slug:
                    return product
        return None

    def get_products(self):
        """Get products list."""
        products_path = os.path.join(
            self.config.GOG_DATA_DIR, 'products.json'
        )
        products = self.load_json(products_path)
        if not products:
            page = self.get_page(1)
            if not page:
                return []
            page_path = self.create_page_path(1)
            products = page['products']
            self.save_json(page_path, page)
            self.save_json(products_path, products)
        return products

    def get_sorted_products(self, key):
        """ Get products sorted by given key.
        """
        products = self.get_products()
        products = self.sort_products(products, key)
        return products

    def get_remote_page(self, page_num):
        """Get remote page from GOG.com API."""
        page_url = self.create_page_url(page_num)
        res = requests.get(
            url=page_url,
            cookies=self.config.GOG_API_COOKIES,
            headers=self.config.GOG_API_HEADERS,
        )
        res = json.loads(res.text) if res.status_code == 200 else None
        return res

    def load_json(self, path):
        """Load json file."""
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as file:
            return json.loads(file.read())

    def parse_page(self, page):
        meta = self.get_page_meta(page)
        keys = ['totalGamesFound', 'totalMoviesFound', 'totalResults', 'ts']
        [page.pop(key) for key in keys]
        page.update(meta)
        return page

    def search_products(self, title):
        products = self.get_products()
        products_found = []
        for product in products:
            if title.lower() in product['title'].lower():
                products_found.append(product)
        return products_found

    def save_json(self, path, data):
        """Save json file."""
        self.create_data_dirs()
        with open(path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2)

    def sort_products(self, products, key):
        """Sort products by given key."""
        if key == 'discount':
            products.sort(key=lambda x: x['price']['discount'], reverse=True)
        elif key == 'price':
            products.sort(key=lambda x: int(x['price']['amount'].replace('.', '')))
        elif key == 'rating':
            products.sort(key=lambda x: x[key], reverse=True)
        else:
            products.sort(key=lambda x: x[key].replace(' ', ''))
        return products

    def update_data(self):
        """Update all data. This takes time and should run as background task.
        """
        meta = self.get_meta()
        if not meta:
            meta = self.create_data_meta()
            if not meta:
                return None

        products = []
        products_path = self.create_products_path()
        meta_path = os.path.join(self.config.GOG_DATA_DIR, 'meta.json')

        for page_num in range(1, meta['totalPages'] + 1):
            page_path = self.create_page_path(page_num)
            page = self.get_remote_page(page_num)
            if page and 'products' in page:
                page = self.parse_page(page)
                products.extend(page['products'])
                self.save_json(page_path, page)
                time.sleep(random.uniform(1.1, 1.9))

        meta['time'] = self.get_curr_time()
        products.sort(key=lambda x: x['slug'])
        self.save_json(products_path, products)
        self.save_json(meta_path, meta)

        print('JOB DONE: Update all data.')
