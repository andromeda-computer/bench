import logging

logging.basicConfig(format='%(levelname)s - %(pathname)s:%(lineno)d - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)