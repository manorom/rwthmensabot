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
        self.mensa_academica = OpenMensaCanteen(187, 'Mensa Academica')
        self.mensa_ahorn = OpenMensaCanteen(95, 'Mensa Ahorn')
        self.mensa_vita = OpenMensaCanteen(96, 'Mensa Vita')
        self.mensa_arg_map = {
            'academica': self.mensa_academica,
            'aca': self.mensa_academica,
            'vita': self.mensa_vita,
            'viter': self.mensa_vita,
            'ahorn': self.mensa_ahorn
        }

    def configure_dispatcher(self, dispatcher):
        dispatcher.add_handler(CommandHandler('mensa', self.mensa_command,
                                              pass_args=True))
        dispatcher.add_handler(CommandHandler('mensavita',
                                             self.mensavita_command,
                                             pass_args=True))
        dispatcher.add_handler(CommandHandler('mensaahorn',
                                              self.mensaahorn_command,
                                              pass_args=True))
        dispatcher.add_handler(CommandHandler('help', self.help))
        logger.info('Configured dispatcher')
        # I dont know how to correctly implement hte control command yet

    def search_parse_canteens(self, args):
        canteen_args = [ self.mensa_arg_map.get(s.lower()) for s in args ]

        canteens = []
        for idx, c in reversed(list(enumerate(canteen_args))):
            if c is not None:
                args.pop(idx)
                canteens.append(c)

        if len(canteens) > 0:
            return canteens
        else:
            return [self.mensa_academica]

    def search_parse_dates(self, args):
        date_args = []
        for idx, arg in reversed(list(enumerate(args))):
            try:
                date = _parse_date(arg)
                args.pop(idx)
                date_args.append(date)
            except ValueError:
                pass
        if len(date_args) > 0:
            return date_args
        else:
            return [datetime.date.today()]


    def mensa_command(self, bot, update, args):
        canteen = self.search_parse_canteens(args)
        self.send_menu(bot, update, args, canteen)

    def mensaahorn_command(self, bot, update, args):
        self.send_menu(bot, update, args, [self.mensa_ahorn])

    def mensavita_command(self, bot, update, args):
        self.send_menu(bot, update, args, [self.mensa_vita])

    def send_menu(self, bot, update, args, canteens):
        dates = self.search_parse_dates(args)

        if len(args) > 0:
            update.message.reply_text(
                message_texts.get_error_unknown_args(args))

        if len(dates) > 1:
            update.message.reply_text(message_texts.get_error_multiple_dates())
            return

        if len(canteens) > 1:
            update.message.reply_text(
                message_texts.get_error_multiple_canteens())
            return

        date = dates[0]
        canteen = canteens[0]

        try:
            menu = canteen.get_menu_by_date(date)
        except CanteenClosedError:
            update.message.reply_text(message_texts.get_error_closed())
        except NoMenuAvailableError:
            update.message.reply_text(message_texts.get_error_no_menu())
        else:  # no exception
            update.message.reply_html(message_texts.get_menu(menu, date, canteen))


    def help(self, bot, update):
        update.message.reply_text(message_texts.get_help())
