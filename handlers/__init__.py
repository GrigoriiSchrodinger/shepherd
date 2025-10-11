from .callback.edit_param import setup_edit_handlers
from .info import setup_info
from .products import setup as setup_products


def setup(dispatcher):
    setup_products(dispatcher)
    setup_info(dispatcher)
    setup_edit_handlers(dispatcher)