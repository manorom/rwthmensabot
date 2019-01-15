import logging
import os
import sys

from telegram.ext import Updater
import click

from mensabot import Mensabot

try:
    from dotenv import load_dotenv, find_dotenv
except ImportError:
    dotenv_imported = False
else:
    dotenv_imported = True


logger = logging.getLogger('mensabot')


def setup_logging(console_loglevel, logfile=None):
    logging.basicConfig(format='%(name)s - %(levelname)-8s %(message)s',
                        level=console_loglevel)
    if logfile:
        file_handler = logging.FileHandler(logfile)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logging.getLogger('').addHandler(file_handler)


def start_polling(updater):
    updater.start_polling()
    logger.info('Updater has started polling.')
    updater.idle()


def start_webhook(updater, port, local_urlpath, webhook_path=None):
    updater.start_webhook(listen="127.0.0.1",
                          port=port,
                          url_path=local_urlpath)
    logger.info('Started webhook server on port 127.0.0.1:{}'.format(port))
    if webhook_path:
        logger.info('Setting webhook path')
        updater.bot.set_webhook(webhook_path)
    updater.idle()


@click.command()
@click.option('--webhook', is_flag=True, default=False)
@click.option('--port', default=0)
@click.option('--debug', is_flag=True)
def main(webhook, port, debug):
    if dotenv_imported:
        load_dotenv(find_dotenv())

    loglevel = logging.INFO
    if debug:
        loglevel = logging.DEBUG

    setup_logging(loglevel)

    # retrieve telegram api token from environment variable
    try:
        token = os.environ['TELEGRAM_TOKEN']
    except KeyError:
        logger.critical("Environment variable `TELEGRAM_TOKEN` was not set.")
        sys.exit(1)

    bot = Mensabot()
    updater = Updater(token)

    bot.configure_dispatcher(updater.dispatcher)

    if webhook:
        logger.info('Using webhook mode')
        if port == 0:
            port = 8080
        start_webhook(updater, port, token)
    else:
        logger.info('Using polling mode')
        start_polling(updater)


if __name__ == '__main__':
    main()
