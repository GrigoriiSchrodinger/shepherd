from .info import setup_info
from .new_user import setup_new_user
from .products import setup as setup_products
from .text_edit import setup_handle_text_edit


def setup(dispatcher):
    setup_products(dispatcher)
    setup_info(dispatcher)
    setup_new_user(dispatcher)
    setup_handle_text_edit(dispatcher)