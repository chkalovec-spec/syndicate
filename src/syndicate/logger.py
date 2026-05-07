import sys
from loguru import logger

logger.remove()
logger.add(
    sys.stdout,
    format="<dim>{time:DD.MM.YYYY HH:mm:ss}</dim> | <level>{message}</level>",
    level="DEBUG",
    colorize=True,
    backtrace=False,
    diagnose=False,
)
