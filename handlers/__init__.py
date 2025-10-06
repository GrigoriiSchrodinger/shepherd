from .start import setup as setup_start
from .products import setup as setup_products

def setup(dispatcher):
    setup_start(dispatcher)
    setup_products(dispatcher)


