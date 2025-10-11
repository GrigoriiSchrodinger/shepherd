from .info import setup_info
from .new_user import setup_new_user
from .products import setup as setup_products


def setup(dispatcher):
    setup_products(dispatcher)
    setup_info(dispatcher)
    setup_new_user(dispatcher)