# Provides formatting functions for dates
# as well as menu, help and error messages.

import datetime
import re


# Maps indices to date names
def get_menu(menu, date, canteen):
    """Returns the whole menu as a string.

    :param menu: The plan that contains the menu
    :param date: The date the plan is for
    :return: A string containing name, price and description of all menu item in
        :const:_MENU_ITEM_ORDER as well as a headline with the date
    """

    formatted_date = get_humanized_date(date)
    date_line = f'<b>{formatted_date} in der {canteen.name}</b>'

    meals = [
        _get_menu_item(menu, meal) for meal in _MENU_ITEM_ORDER if meal in menu
    ]
    hauptbeilagen = ' '.join(menu['Hauptbeilagen']['name'])
    nebenbeilagen = ' '.join(menu['Nebenbeilage']['name'])
    side_dishes = '<i>Beilagen</i>\n' \
                  '{}\n' \
                  '{}'.format(hauptbeilagen, nebenbeilagen)

    menu_parts = [date_line, *meals, side_dishes]
    return '\n\n'.join(menu_parts)


# Influences the order of display
_MENU_ITEM_ORDER = [
    'Tellergericht',
    'Süßspeise',
    'Vegetarisch',
    'Klassiker',
    'Empfehlung des Tages',
    'Pasta',
    'Burger der Woche',
    'Burger'
]


def get_humanized_date(date):
    """Returns the date as an easily readable string.
    Takes the form `heute, 10.09.2016` or `Samstag, 10.09.2016`, depending on
    suitability of relative references `heute`, `morgen`, `übermorgen` and
    `gestern`.

    :param date: The date to humanize.
    :return: The localized date prefixed with e. g. 'Heute' or 'Mittwoch'
    """

    days_difference = (date - datetime.date.today()).days

    prefix = None
    if days_difference == 0:
        prefix = _INDEX_TO_DATE[10]  # Heute
    elif days_difference == 1:
        prefix = _INDEX_TO_DATE[11]  # Morgen
    elif days_difference == 2:
        prefix = _INDEX_TO_DATE[12]  # Übermorgen
    elif days_difference == -1:
        prefix = _INDEX_TO_DATE[20]  # Gestern

    date_parts = [_INDEX_TO_DATE[date.weekday()], date.strftime('der %d.%m.%Y')]
    if prefix is not None:
        date_parts.insert(0, prefix)
    return ", ".join(date_parts)


_INDEX_TO_DATE = {
    0: 'Montag',
    1: 'Dienstag',
    2: 'Mittwoch',
    3: 'Donnerstag',
    4: 'Freitag',
    5: 'Samstag',
    6: 'Sonntag',
    10: 'Heute',
    11: 'Morgen',
    12: 'Übermorgen',
    20: 'Gestern',
}

_MENU_ITEM_EMOJIS = {
    'Tellergericht': '🍲',
    'Süßspeise': '🍰',
    'Vegetarisch': '🥗',
    'Klassiker': '🍗',
    'Empfehlung des Tages': '🥘',
    'Pasta': '🍝',
    'Burger der Woche': '🍔',
    'Burger': '🍔',
}


def _get_menu_item(menu, name):
    """Returns a string containing the entry in the menu.
    The item to be displayed is taken from `plan` using `name` as the key.

    :param menu: The plan that contains the menu (a dict)
    :param name: The name of the menu item to be displayed
    :returns: HTML String with category name, price and item description
    """
    meal = menu[name]

    price_suffix = ' — {:.2f}€'.format(meal['price']) if meal['price'] else ''
    header = '<i>{name}</i>{price_suffix}'.format(name=name,
                                                  price_suffix=price_suffix)

    description = _get_description(meal, name)

    return '\n'.join([header, description])



def _get_description(meal, category):
    all_descriptions = []
    for meal_idx, meal_name in enumerate(meal['name']):
        description_parts = re.split(r' \| | mit ', meal_name)

        supplements_description = ''
        if len(description_parts) == 2:
            supplements_description = ' mit {}'.format(description_parts[1])
        elif len(description_parts) > 2:
            supplements_description = ' mit {middle} & {last}'.format(
                middle=', '.join(description_parts[1:-1]), last=description_parts[-1]
            )

        vegan_vegetarian_desc = ''
        if 'OLV' in meal['notes'][meal_idx]:
            vegan_vegetarian_desc = ' <i>(vegetarisch)</i>'
        if 'vegan' in meal['notes'][meal_idx]:
            vegan_vegetarian_desc = ' <i>(vegan)</i>'

        all_descriptions.append(
            '{emoji} <b>{name}</b>{vegan_vegetarian}'
            '{supplements}'.format(name=description_parts[0],
                                   vegan_vegetarian=vegan_vegetarian_desc,
                                   supplements=supplements_description,
                                   emoji=_MENU_ITEM_EMOJIS.get(category, ''))
        )

    return '\n'.join(all_descriptions)


# ---------------------------------
# Additional text
# ---------------------------------

# noinspection PyPep8
_HELP_TEXT = """
Dieser Bot gibt den Speiseplan der Mensa Academica an der RWTH Aachen aus.

/mensa - für den heutigen Speiseplan
/mensa `Tag` - sendet den Speiseplan für den gewählten `Tag`. Dabei kann `Tag` unter anderem `heute`, `Mittwoch` oder ein Datum im Format `YYYY-MM-DD` sein.
"""


def get_help():
    """Returns the help message for this bot."""
    return _HELP_TEXT


# ---------------------------------
# Error text
# ---------------------------------

# noinspection PyPep8
_DATEFORMAT_ERROR_TEXT = """
Das Datumsformat habe ich nicht verstanden.
Bitte benutze für ein Datum das Format `YYYY-MM-DD`. Du kannst auch `morgen` oder einen Wochentag wie `Mittwoch` oder kurz `mi` eingeben.
"""


def get_error_dateformat():
    """Returns an error message signifying that the date's format was not recognized."""
    return _DATEFORMAT_ERROR_TEXT


_NOMENU_ERROR_TEXT = 'Für diesen Tag ist kein Speiseplan verfügbar.'
_CLOSED_ERROR_TEXT = 'An diesem Tag ist die Mensa geschlossen.'


def get_error_no_menu():
    return _NOMENU_ERROR_TEXT


def get_error_closed():
    return _CLOSED_ERROR_TEXT

def get_error_unknown_args(args):
    if len(args) > 1:
        return 'Ich habe die Befehle "{}" nicht verstanden'.format(
            ", ".join(args)
        )
    else:
        return f'Ich habe den Befehl "{args[0]}" nicht verstanden'

def get_error_multiple_dates():
    return 'Ich kann nur das Menü für einen Tag auf einmal senden'

def get_error_multiple_canteens():
    return 'Ich kann nur das Menü für eine Mensa auf einmal senden'
