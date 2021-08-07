from datetime import datetime

from flask import jsonify, redirect, render_template, request

from . import app, config, gogapi, sched
from .forms import SearchForm


RESPONSE_API_PAGE_404 = {'message': 'Page not found.'}
RESPONSE_API_UPDATE = {'message': 'Update started.'}


@app.context_processor
def add_context_globals():
    """ Add globals to all views.
    """
    return {
        'search_form': SearchForm()
    }


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/products')
def products_query():

    # Get query params or set default values
    search_query = request.args.get('search', None, str)
    sort_param = request.args.get('sort', config.SORT_PARAMS[0], str)
    curr_page = request.args.get('page', 1, int)

    # Route must contain sort and page params
    if not request.args.get('sort') or not request.args.get('page'):
        url_prefix = '&' if len(request.args) > 0 else '?'
        url = f'{request.url}{url_prefix}sort={sort_param}&page={curr_page}'
        return redirect(url)

    products = []
    if search_query:
        products = gogapi.search_products(search_query)
        products = gogapi.sort_products(products, sort_param)
    else:
        products = gogapi.get_sorted_products(sort_param)

    # Calculate pagination settings
    page_start = (curr_page - 1) * config.PAGINATION_LENGTH
    page_stop = page_start + config.PAGINATION_LENGTH
    products_sliced = products[page_start:page_stop]
    total_pages = len(products) / config.PAGINATION_LENGTH
    if type(total_pages) == float:
        total_pages = int(total_pages) + 1

    # Re-route to nearest if page number is out of bound
    if curr_page < 1:
        return redirect(request.url.replace(f'{curr_page}', '1'))
    elif curr_page > total_pages:
        return redirect(request.url.replace(f'{curr_page}',
            str(total_pages)))

    last_update = ''
    meta = gogapi.get_meta()
    if meta and 'time' in meta:
        last_update = datetime.fromtimestamp(meta['time'])

    ctx = {
        'current_page': curr_page,
        'last_update': last_update,
        'products': products_sliced,
        'sort_params': config.SORT_PARAMS,
        'total_pages': total_pages,
        'total_products': len(products)
    }
    return render_template('products.html', **ctx)


@app.route('/products/search', methods=('POST',))
def products_search():
    """ Search products by title.
    """
    form = SearchForm()
    if form.validate_on_submit():
        title = form.title.data
        return redirect(f'/products?search={title}')
    return redirect('/products')


@app.route('/products/')
def products():
    return redirect('/products?sort=title&page=1')


@app.route('/products/<product_slug>/')
def product(product_slug):
    product = gogapi.get_product_by_slug(product_slug)
    if product:
        return render_template('product.html', product=product)
    return redirect('/')


@app.route('/api/')
def api_home():
    return redirect('/api/pages/1/')


@app.route('/api/pages/')
def api_pages():
    return redirect('/api/pages/1/')


@app.route('/api/pages/<int:page_num>/')
def api_page_num(page_num):
    page = gogapi.get_page(page_num)
    if page:
        return jsonify(page)
    return jsonify(RESPONSE_API_PAGE_404), 404


@app.route('/api/products/')
def api_products():
    products = gogapi.get_products()
    return jsonify(products)


@app.route('/api/update/')
def api_update():
    sched.add_job('update_data', gogapi.update_data)
    return jsonify(RESPONSE_API_UPDATE), 302
