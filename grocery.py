"""
A command line interface for interacting with a toy shopping cart.
"""
import functools
import json
import os
import re
import time

import click
import ilock


# Putting a data file in the same directory as this file is fairly safe...
#  ends up being stylistically a little strange when this file is installed as
#  a library, but without knowing what type of system this might be installed
#  on this seems like the most reliable thing to do.
CART_DB_PATH = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), '.grocery_cart.json'
)
STORE_DB_PATH = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), '.store_products.json'
)
HEADER = 'ID,Name,Unit of Measure,Quantity,Price'


_format_price = '${:,.2f}'.format


def _write_json(data, cart=True):
    '''
    Read serialized product file from disk.
    '''
    path = CART_DB_PATH
    if not cart:
        path = STORE_DB_PATH
    with open(path, 'w') as filehandle:
        json.dump(data, filehandle)


def _write_cart(data):
    _write_json(data)


def _write_products(data):
    _write_json(data, False)


def _read_json(cart=True):
    '''
    Given a dictionary representation of a shopping cart, write it to disk in
    json serialization.
    '''
    path = CART_DB_PATH
    if not cart:
        path = STORE_DB_PATH
    # Cart is empty if file doesn't exist.
    ret = {}
    if os.path.isfile(path):
        with open(path, 'r') as filehandle:
            ret = json.load(filehandle)
    # Keys are always stored as strings in json so transform them
    #   back to integers.
    return {int(key): val for key, val in ret.items()}


def _read_products():
    return _read_json(False)


def _read_cart():
    return _read_json(True)


def _lock(wrapped_func):
    '''
    Decorator which ensures the wrapped function with run only with the
    shopping cart filesystem lock acquired.
    '''
    @functools.wraps(wrapped_func)
    def wrapper(*args, **kwargs):
        try:
            with ilock.ILock('grocery cart lock', timeout=5):
                return wrapped_func(*args, **kwargs)
        except ilock.ILockException:
            raise click.ClickException('Unable to acquire grocery cart lock '
                    'after 5 seconds.') from None
    return wrapper


def _read_json_with_lock(cart=True):
    def _read_json_decorator(wrapped_func):
        '''
        Decorator which passes the de-serialized product list to the wrapped
        function as keyword argument, and ensures the mutex is acquired for the
        read.
        '''
        @functools.wraps(wrapped_func)
        @_lock
        def wrapper(*args, **kwargs):
            kwargs['data'] = _read_json(cart)
            return wrapped_func(*args, **kwargs)
        return wrapper
    return _read_json_decorator


@click.group()
def cart():
    '''
    CLI for interacting with a grocery cart. See "cart COMMAND --help" for more
    detail about subcommands.
    '''
    pass


@click.group()
def store():
    '''
    CLI for interacting with a grocery store. See "products COMMAND --help" for
    more detail about subcommands.
    '''
    pass


@cart.command()
@_lock
def sleep():
    '''
    Sleep for ten seconds while holding the database lock. Only really useful
    for testing.
    '''
    time.sleep(10)


@store.command()
@click.argument('name', nargs=1)
@click.argument('units', nargs=1)
@click.argument('price', nargs=1, type=float)
@_lock
def add_item(name, units, price):
    '''
    Add a new item to the product list. Each item has a name (string), unit
    price ($, given as a float), and unit description (kg., liters, loafs,
    pies, boxes, cases, etc.).
    '''
    _add_item(name, units, price, None)


@cart.command()
@click.argument('name', nargs=1)
@click.argument('units', nargs=1)
@click.argument('price', nargs=1, type=float)
@click.argument('quantity', default=1, type=float)
@_lock
def add_item(name, units, price, quantity):
    '''
    Add a new item to the shopping cart. Each item has a name (string), unit
    price ($, given as a float), and unit description (kg., liters, loafs,
    pies, boxes, cases, etc.).
    The number of units, as defined in the units entry, may also be given.
    Quantity defaults to 1 and accepts reals greater than zero.'
    '''
    if quantity is not None and quantity <= 0:
        raise click.BadParameter('Quantity must be greater than zero.',
          param_hint='quantity')
    product_id = _add_item(name, units, price)
    _add_item(quantity=quantity, product_id=product_id)


def _add_item(name=None, units=None, price=None, quantity=None,
        product_id=None):
    if price is not None and price <= 0:
        raise click.BadParameter('Price must be greater than zero.',
          param_hint='price')
    if quantity is not None and quantity <= 0:
        raise click.BadParameter('Quantity must be greater than zero.',
          param_hint='quantity')
    products = _read_json(quantity is not None)
    # The new id is one plus the previous largest id or 0 if products is empty.
    item = {'product_id': product_id}
    if product_id is None:
        item = {'Name': name, 'Unit of Measure': units, 'Price': price}
    if quantity is not None:
        item['Quantity'] = quantity
    ret = 0 if not products else max(products) + 1
    products[ret] = item
    _write_json(products, quantity is not None)
    return ret


@store.command()
@click.option('--ascending/--descending', default=True, help='Sort direction.')
@click.option('--sortby', help='The column to sort by.',
        type=click.Choice(['Name', 'Price', 'ID']), default='ID')
def view(ascending, sortby):
    '''
    Display current product listings. Contents are displayed with
    subtotals and can be sorted multiple ways.
    '''
    _read_json_with_lock(False)(_view)(ascending, sortby, cart=False)


@cart.command()
@click.option('--ascending/--descending', default=True, help='Sort direction.')
@click.option('--sortby', help='The column to sort by.',
        type=click.Choice(['Name', 'Subtotal', 'Price', 'ID']), default='ID')
def view(ascending, sortby):
    '''
    Display current shopping cart contents. Contents are displayed with
    subtotals and can be sorted multiple ways.
    '''
    _read_json_with_lock()(_view)(ascending, sortby)


def _view(ascending, sortby, data=None, cart=True):
    if not data:
        click.echo('Empty.')
        return
    header = HEADER.split(',')
    products = None
    if cart:
        # Create new column for subtotal.
        header.append('Subtotal')
        # Keep total of subtotals to display grand total at end.
        total = 0
    else:
        header.remove('Quantity')
    rows = []
    for idx, row in data.items():
        if 'product_id' in row:
            if products is None:
                products = _read_products()
            row.update(products[row['product_id']])
            row.pop('product_id')
        if cart:
            # calculate subtotal and update grand total.
            row['Subtotal'] = row['Price'] * row['Quantity']
            total += row['Subtotal']
        row['ID'] = str(idx)
        rows.append(row)
    # Sort values before string formatting.
    rows = sorted(rows, key=lambda x: x[sortby], reverse=not ascending)
    # Keep track of widest item in column to help with text formatting.
    col_width = {label: len(label) for label in header}
    for row in rows:
        # format other columns as strings
        row['Price'] = _format_price(row['Price'])
        if cart:
            row['Subtotal'] = _format_price(row['Subtotal'])
            row['Quantity'] = '{}'.format(row['Quantity'])
        # Update maximum column widths if any of the strings are longer than
        #    previous values.
        col_width = {label: max(col_width[label], len(row[label]))
            for label in header}
    if cart:
        total = _format_price(total)
        # Ensure that the grand total will fit in the subtotal columns.
        col_width['Subtotal'] = max(col_width['Subtotal'], len(total))
    # Create format string for each column which can be used to pad values in
    # that column.
    col_width = {label: ' {{: <{}}}'.format(width) for label, width in
        col_width.items()}
    # Format each row of the cart.
    lines = [
      ' |'.join([col_width[col].format(row[col]) for col in header])
      for row in rows
    ]
    # add header and total lines and some horizontal lines.
    if cart:
        lines.append('-' * max(len(line) for line in lines))
        lines.append('  '.join(col_width[col].format(val) for col, val in
            zip(header, ['', 'Total', '', '', '', total])))
    lines.insert(0, ' |'.join(col_width[col].format(col) for col in header))
    lines.insert(1, '-' * max(len(line) for line in lines))
    # combine rows and print.
    lines = '\n'.join(lines)
    click.echo(lines)


@store.command()
@click.argument('product_id', nargs=1, type=int)
@click.argument('quantity', nargs=1, type=float)
@_lock
def to_cart(product_id, quantity):
    '''
    Add product with id to cart in given quantity.
    '''
    cart = _read_cart()
    products = _read_products()
    if product_id not in products:
        raise click.BadParameter('Error: item with id [{}] not found in '
                'products.'.format(product_id), param_hint='product_id')
    item = products[product_id]
    _add_item(quantity=quantity, product_id=product_id)


@store.command()
@click.argument('product_id', nargs=1, type=int)
@_lock
def remove(product_id):
    '''
    Delete products list item by ID.
    '''
    # First remove all appearances of the product in the cart
    cart = _read_cart()
    cart = {key: val for key, val in cart.items()
            if val.get('product_id', None) != product_id}
    _write_json(cart)
    # Now remove the product from the listing
    _remove(product_id, False)


@cart.command()
@click.argument('item_id', nargs=1, type=int)
@_lock
def remove(item_id):
    '''
    Delete shopping cart item by ID.
    '''
    _remove(item_id)

def _remove(item_id, cart=True):
    data = _read_json(cart)
    if item_id not in data:
        raise click.BadParameter('Error: item with id [{}] not found in '
                '{}.'.format(item_id, 'cart' if cart else 'products'),
                param_hint='item_id' if cart else 'product_id')
    data.pop(item_id)
    _write_json(data, cart)


def billing_prompt(query, pattern):
    value = click.prompt(query)
    if not re.compile(pattern).match(value):
        raise click.UsageError('Invalid response format.')
    return value


def _card_auth(card, code, date, zipcode):
    '''Just exists as a handle for tests to check inputs'''
    pass


@cart.command()
@click.argument('method', nargs=1, type=click.Choice(['card', 'paypal']))
@_read_json_with_lock()
def checkout(data, method):
    '''
    Enter billing information and confirm items. Argument is a choice of
    payment method.
    '''
    if not data:
        click.echo('Please add items to cart before checking out.')
        return
    if method == 'card':
        number = billing_prompt('Please enter credit card number (no dashes)',
                r'^\d{16}$')
        security_code = billing_prompt('Please enter 3 digit credit card '
                 'security code', r'^\d{3}$')
        expire_date = billing_prompt('Please enter credit card'
                ' expiration date (MMYY)', r'^\d{4}$')
        if expire_date[:2] == '00' or int(expire_date[:2]) > 12:
            raise click.UsageError('Month must be in [1-12]')
        zip_code = billing_prompt('Please enter billing zip code', r'^\d{5}$')
        shipping_address = click.prompt('Please enter shipping address')
        click.echo('stealing your money (kidding...)')
        _card_auth(number, security_code, expire_date, zip_code)
        click.echo('card number: ************{}'.format(number[-4:]))
        click.echo('shipping address: {}'.format(shipping_address))
    if method == 'paypal':
        email = billing_prompt('Please enter paypal account email',
                r'^.+@[^.].+\..+[^.]$')
        # authenticate through paypal, don't take passwords directly, etc, etc.
        click.echo('Authenticating with paypal using [{}]...'.format(email))
        if not click.confirm('Use paypal shipping address?'):
            shipping_address = click.prompt('Please enter shipping address')
    _read_json_with_lock()(_view)(True, 'ID')
    if click.confirm('Confirm order and payment details?'):
        # charge money, begin transaction, etc, then empty the cart.
        _empty()
        click.echo('Thank you for your purchase!')


@cart.command()
@click.argument('item_id', nargs=1, type=int)
@click.argument('new_quantity', nargs=1, type=float)
@_lock
def update_quantity(item_id, new_quantity):
    '''
    Update the quantity of units for an item in the shopping cart.
    The item is identified by its id and the new quantity is a real greater
    than zero.
    '''
    if new_quantity <= 0:
        raise click.BadParameter('Quantity must be greater than zero.',
          param_hint='new_quantity')
    # load the preexisting cart data.
    cart = _read_json()
    if item_id not in cart:
        raise click.BadParameter('Error: item with id [{}] not found in '
                'cart.'.format(item_id), param_hint='item_id')
    # Update the quantity of the given item
    cart[item_id]['Quantity'] = new_quantity
    # Write the update back to disk.
    _write_json(cart)


@cart.command()
def empty():
    '''
    Delete all items in the shopping cart.
    '''
    _empty()


@store.command()
def clear():
    '''
    Delete all items in the products list.
    '''
    _empty(False)


@_lock
def _empty(cart=True):
    # simply write an empty cart to disk.
    _write_json({}, cart)
    click.echo('{} cleared.'.format('Cart' if cart else 'Products list'))
