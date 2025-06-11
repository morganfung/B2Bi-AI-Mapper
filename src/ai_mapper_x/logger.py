from starlette_context import context
import logging


class ContextFilter(logging.Filter):
    def filter(self, record):
        record.transaction_id = getattr(context, 'transaction_id', "N/A")
        return True
    

def setup_app_logger():
    """setup app logger

    Returns: None
    """
    logger = logging.getLogger("aimapper")
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(transaction_id)s - %(levelname)s - %(message)s')

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    logger.addFilter(ContextFilter())
    logger.addHandler(ch)

    return logger


logger = setup_app_logger()