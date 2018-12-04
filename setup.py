from setuptools import setup

setup(
    name='grocery',
    version='0.1',
    py_modules=['grocery'],
    install_requires=[
        'click==6.7',
        'ilock==1.0.1',
    ],
    entry_points='''
        [console_scripts]
        cart=grocery:cart
        products=grocery:store
    ''',
)
