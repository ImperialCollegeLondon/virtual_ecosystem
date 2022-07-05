import logging

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] - %(module)s - %(funcName)s(%(lineno)d) - %(message)s",
)

loggers = logging.getLogger(__name__)
