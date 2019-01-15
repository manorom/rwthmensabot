import datetime
from collections import namedtuple
import logging

from telegram.ext import CommandHandler

from . import message_texts
from .openmensa import OpenMensaCanteen, NoMenuAvailableError, CanteenClosedError

logger = logging.getLogger(__name__)

# ---------------------------------
# Date functionality
# ---------------------------------

# Maps weekdays to `datetime`'s numerical representation
_WEEKDAYS = {
    'montag': 0, 'mo': 0,
    'dienstag': 1, 'di': 1,
    'mittwoch': 2, 'mi': 2,
    'donnerstag': 3, 'do': 3,
    'freitag': 4, 'fr': 4,
    'samstag': 5, 'sa': 5,
    'sonntag': 6, 'so': 6,
}

DateFormat = namedtuple('DateFormat', ['format', 'year_missing'])

_DATE_FORMATS = (
    DateFormat(format='%d.%m', year_missing=True),
    DateFormat(format='%d.%m.', year_missing=True),
    DateFormat(format='%d.%m.%y', year_missing=False),
    DateFormat(format='%Y-%m-%d', year_missing=False),
    DateFormat(format='%d.%m.%Y', year_missing=False)
)


def _parse_date(date_input):
    """Parses a date from the input.
    Supports `YY-MM-DD` format and keywords such as 'heute'.

    :param date_input: The raw input to parse the date from
    :return: A datetime.date object representing the input date
    :raises ValueError: if date is not keyword and not in ISO format.
    """
    date_input = date_input.lower()
    today = datetime.date.today()

    if date_input in ['heute', 'today']:
        date = today
    elif date_input in ['morgen', 'tomorrow']:
        date = today + datetime.timedelta(days=1)
    elif date_input in ['übermorgen']:
        date = today + datetime.timedelta(days=2)
    elif date_input in ['gestern', 'yeserday']:
        date = today - datetime.timedelta(days=1)
    elif date_input in _WEEKDAYS:
        difference = (_WEEKDAYS[date_input] - today.weekday()) % 7
        date = today + datetime.timedelta(days=difference)
    else:
        # Try different date formats
        for date_format in _DATE_FORMATS:
            try:
                date = datetime.datetime.strptime(date_input,
                                                  date_format.format).date()
                if date_format.year_missing:
                    date = date.replace(year=today.year)
                break  # found working format, don't try others
            except ValueError:
                pass
        else:
            raise ValueError()

    return date


# ---------------------------------
# Mensabot
# ---------------------------------

class Mensabot(object):
    def __init__(self):
        self.mensaAcademica = OpenMensaCanteen(187)

    def configure_dispatcher(self, dispatcher):
        dispatcher.add_handler(CommandHandler('mensa', self.mensa,
                                              pass_args=True))
        dispatcher.add_handler(CommandHandler('help', self.help))
        logger.info('Configured dispatcher')
        # I dont know how to correctly implement hte control command yet

    def mensa(self, bot, update, args):
        """ Sends the menu.
        If the date is invalid, an error message will be sent.
        If the command is not supported, nothing will be done.

        :param input_message: The raw input user message.
        """

        # Parse Args
        if len(args) == 0:  # we have just /mensa without a date
            date = datetime.date.today()
        elif len(args) == 1:  # /mensa with date
            try:
                date = _parse_date(args[0])
            except ValueError:
                # return message_texts.get_error_dateformat() here
                return
        else:  # unsupported number of arguments
            # todo: issue some kind of error
            return

        # Retrieve menu
        try:
            menu = self.mensaAcademica.get_menu_by_date(date)
        except CanteenClosedError:
            update.message.reply_text(message_texts.get_error_closed())
        except NoMenuAvailableError:
            update.message.reply_text(message_texts.get_error_no_menu())
            pass
        else:  # no exception
            update.message.reply_html(message_texts.get_menu(menu, date))

    def help(self, bot, update):
        update.message.reply_text(message_texts.get_help())

    def control(self, bot, update):
        # todo: figure out how to implement this
        pass
