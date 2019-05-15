import datetime
from threading import RLock
import logging
import re
from typing import Dict, Any

import requests


logger = logging.getLogger(__name__)

# ---------------------------------
# Constants and Magic Values
# ---------------------------------

_CLOSED = object()
_OPENMENSA_MEAL_URL = 'http://openmensa.org/api/v2/canteens/{}/days/{}/meals'
_CACHE_SIZE = 7
_CACHE_KEEP_DAYS = datetime.timedelta(days=7)
_REQUESTS_HEADERS = {'User-Agent': '@rwthmensabot Telegram Bot. Please '
                                   '@rcurve on telegram in case of problems'}


# ---------------------------------
# Mensa Cache
# ---------------------------------

class OpenMensaCacheEntry(object):
    def __init__(self, cache_value : Dict[str, Any],
                 good_through: datetime.datetime):
        self.cache_value: Dict[str, Any] = cache_value
        self.good_through: datetime.datetime = good_through
        self.last_used: datetime.datetime = datetime.datetime.now()

# We use a Mutex when altering the cache. This incurs some overhead but we
# switched our exec model before to a multi-threaded one and we might want
# to use multi threaded features from ptb at some point.
class OpenMensaCache(object):
    def __init__(self, cache_size: int):
        self._cache_data: Dict[datetime.date, OpenMensaCacheEntry] = {}
        self._cache_size: int = cache_size
        self._mutex = RLock()
    def _remove_expired(self):
        now = datetime.datetime.now()
        to_be_removed = [k for k,v in self._cache_data.items() if v.good_through < now]
        for k in to_be_removed:
            self._cache_data.pop(k)
    def _remove_least_recently_used(self):
        lru_key = min(self._cache_data.keys(),
                      key=lambda k: self._cache_data[k].last_used)
        self._cache_data.pop(lru_key)
    def encache(self, date: datetime.date, cache_value: Dict[str, Any],
                good_through: datetime.datetime):
        with self._mutex:
            if len(self._cache_data) >= self._cache_size:
                self._remove_expired()
            # The cache should never have more than _cache_size entries.
            # But just to be sure whe make this a while loop.
            while len(self._cache_data) >= self._cache_size:
                self._remove_least_recently_used()
            self._cache_data[date] = OpenMensaCacheEntry(cache_value, good_through)
    def get(self, date: datetime.date) -> Dict[str, Any]:
        with self._mutex:
            if not date in self._cache_data:
                raise KeyError()
            if self._cache_data[date].good_through <= datetime.datetime.now():
                del self._cache_data[date]
                raise KeyError()
            self._cache_data[date].last_used = datetime.datetime.now()
        return self._cache_data[date].cache_value
    def flush(self):
        with self._mutex:
            self._cache_data = {}


# ---------------------------------
# Exceptions
# ---------------------------------

class NoMenuAvailableError(Exception):
    """No menu is available. Most generic exception."""


class CanteenClosedError(NoMenuAvailableError):
    """Canteen is closed. No menu is available."""


# ---------------------------------
# Helper functions
# ---------------------------------


def _validate_date(date: datetime.date):
    """Validates the date to be in range and a weekday.

    :param date: This date's validity will be checked.
    :raises CanteenClosed: if there is no plan on the requested date because
                           the canteen is closed.
    :raises NoMenuAvailableError: if the date is out of range

    """

    # Check for weekday
    if date.weekday() in [5, 6]:
        raise CanteenClosedError()

    # Validate range
    if date > datetime.date.today() + datetime.timedelta(days=7) \
            or date < datetime.date.today() - datetime.timedelta(days=7):
        raise NoMenuAvailableError()


def _make_dict_from_response(response: Dict):
    """Formats the JSON response as a dictionary.
    If the canteen is closed, the string 'closed' is returned instead of a
    dictionary.

    :param response: OpenMensa's response in JSON format
    :return: The response formatted as a dictionary, or the string 'closed',
             if the canteen is closed.
    :rtype: dict|string
    """

    dictionary: Dict[str, Any] = {}
    if all(map(lambda meal: 'geschlossen' in meal['name'], response)):
        return _CLOSED

    for meal in response:
        category = meal['category']

        # Clean up description
        # Remove multiple whitespace
        description = re.sub(
            r' +',
            r' ',
            meal.get('name')
        )
        # Remove whitespace before comma
        description = re.sub(
            r'\s+,',
            r',',
            description
        )

        # If entry for category already exists, append new description
        if category in dictionary:
            dictionary[category]['name'] = dictionary[category]['name'] + \
                                           '\n' + description
        else:  # Make new entry
            dictionary[category] = {'name': description,
                                    'price': meal.get('prices', {})
                                                 .get('students')}

    return dictionary


# ---------------------------------
# Canteen
# ---------------------------------


class OpenMensaCanteen(object):
    def __init__(self, openmensa_id=187):
        self.id = openmensa_id
        self._cache: OpenMensaCache = OpenMensaCache(_CACHE_SIZE)

    # locale.setlocale(locale.LC_TIME, 'de_DE')

    def get_menu_by_date(self, date: datetime.date) -> Dict:
        """Returns the menu for the given date.

        :param date: The menu's date.
        :return: A menu.
        :rtype: dict
        :raises NoMenuAvailableError: if there is no menu for the requested date.
        """
        _validate_date(date)

        try:
            menu = self._cache.get(date)
            logger.debug('Plan for date %s found in cache. Returning.', date.isoformat())
        except KeyError:
            logger.debug('Plan for date %s not in cache. Loading.', date.isoformat())
            menu = self._retrieve_menu(date)
            encache_until = self._encache_until_datetime(date, menu)

            if encache_until is not None:
                self._cache.encache(date, menu, encache_until)

        if menu is None:
            raise NoMenuAvailableError()
        if menu is _CLOSED:
            raise CanteenClosedError()

        return menu

    def _retrieve_menu(self, date: datetime.date) -> Any[Dict, None]:
        raw_response = requests.get(_OPENMENSA_MEAL_URL.format(self.id,
                                        date.isoformat()),
                                        headers=_REQUESTS_HEADERS)
        if raw_response.text == ' ':
            return None

        json_response = raw_response.json()
        return _make_dict_from_response(json_response)

    def _encache_until_datetime(self, date: datetime.date, menu) -> Any[datetime.datetime, None]:
        # Decides for how long a response should be cached by OpenMnesaCache
        # Returns None if it should not be cached
        if menu is None: # We dont have a menu yet, cache not so long
            pass
        # responses for more than a few days ago are unlikely to be requested often -> do not ache
        if datetime.date.today() - date >= datetime.timedelta(days=2):
            return None
        # Cache everything else for at most _CACHE_KEEP_DAYS days
        return datetime.datetime.now() + _CACHE_KEEP_DAYS

