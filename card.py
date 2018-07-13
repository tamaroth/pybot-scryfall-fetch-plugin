"""
    A plugin to display Magic: the Gathering card information.
"""

import json
import urllib

from plugin import *


# Address of Scryfall API.
SCRYFALL_API_ADDRESS = 'https://api.scryfall.com'


class NoCardError(Exception):
    """Requested card was not found."""

    def __init__(self):
        self.msg = 'Couldn\'t find the requested card!'


class NoDataToParseError(Exception):
    """Data to parse does not exist."""

    def __init__(self, location):
        self.msg = f'There is no data to parse: {location}'


class CardParser:
    """Parses the given card data (in JSON) into list of text.

    :param JSON card_data: The data in JSON form of the card.
    """

    def __init__(self, card_data):
        if not card_data:
            raise NoDataToParseError('card_data')
        self._card_data = card_data
        self._info = card_data[0]

    @property
    def name(self):
        """Returns the parsed name of the card."""
        _verify_data_key_exists('name')
        return f'{color.purple(self._info["name"])}'

    @property
    def mana_cost(self):
        """Returns the parsed cost of the card."""
        _verify_data_key_exists('mana_cost')
        return f'{self._decorate_mana_cost(self._info["mana_cost"])}'

    @property
    def rarity(self):
        """Returns the parsed rarity of the card."""
        _verify_data_key_exists('rarity')
        rarity = {
            'common': f'{color.black("common")}',
            'uncommon': f'{color.light_grey("uncommon")}',
            'rare': f'{color.blue("rare")}',
            'mythic': f'{color.orange("mythic")}'
        }
        for key, value in rarity.items():
            if key == self._info['rarity']:
                return value
        return 'unknown rarity!'

    @property
    def type(self):
        """Returns the parsed type of the card."""
        _verify_data_key_exists('type_line')
        return self._info['type_line']

    @property
    def oracle_text(self):
        """Returns the parsed oracle text of the card as a list."""
        if 'oracle_text' not in self._info:
            return []
        return self._decorate_mana_cost(self._info['oracle_text']).split('\n')

    @property
    def pt(self):
        """Returns the parsed power/thoughtness of the card (if present)."""
        if not all (k in self._info for k in ('power', 'toughness')):
            return ''

        p = self._info['power']
        t = self._info['toughness']
        return f'{p}/{t}'

    @property
    def sets(self):
        """Returns the parsed list of sets in which the card is available."""
        sets = 'Available sets:'
        for card in cls.card_data:
            if 'set' in card:
                sets += card['set'].upper()
        return sets

    def _decorate_mana_cost(self, text):
        colours = {
            '{W}': f'{color.yellow("{W}")}',
            '{U}': f'{color.blue("{U}")}',
            '{R}': f'{color.red("{R}")}',
            '{B}': f'{color.black("{B}")}',
            '{G}': f'{color.green("{G}")}'
        }
        for key, value in colours.items():
            text = text.replace(key, value)

    def _verify_data_key_exists(self, data_key):
        """Verifies that the data key exists in the card info."""
        if data_key not in self._info:
            raise NoDataToParseError(data_key)


class Scryfall:
    """Fetches card information from ScryFall.com."""

    @staticmethod
    def get_card_data(card_name=None):
        """Retrieve card details from ScryFall."""
        try:
            return _fetch_card_details(card_name)
        except NoCardError as err:
            return [err.msg]

    @staticmethod
    def _fetch_card_details(card_name):
        """Fetches the text detail of the card."""

        if card_name is None:
            endpoint = '/cards/random'
        else:
            endpoint = f'/cards/search?q={"+".join(card_name)}'

        cards = _fetch_card_data(f'{SCRYFALL_API_ADDRESS}{endpoint}')
        for card in cards:
            name = card['name']
            uri = card['prints_search_uri']
            if name.lower() == ' '.join(card_name).lower():
                return _fetch_card_data(uri)
            possible_cards[name] = uri

        if len(possible_cards) > 1:
            return ['Possible cards: ', '|'.join(possible_cards)]

        _, uri = possible_cards.popitem()
        return _fetch_card_data(uri)

    @staticmethod
    def _fetch_card_data(uri):
        """Fetches the raw data from the URI."""
        try:
            with urllib.request.urlopen(uri) as response:
                return json.loads(response.read().decode('utf-8'))['data']
        except (urllib.error.URLError, urllib.error.HTTPError, UnicodeDecodeError):
            raise NoCardError


class Card:
    """A single card.

    :param str card_name: Full or partial name of the card to fetch.
    """

    def __init__(self, card_name=None):
        self._card_data = Scryfall.get_card_data(card_name)

    @property
    def formatted(self):
        """Returns a list of lines that describe the given card."""
        try:
            parser = CardParser(self._card_data)
            return [
                f'{parser.name} {parser.cost} |{parser.type}|{parser.pt} - {parser.rarity}',
                parser.oracle_text,
                parser.sets
            ]
        except NoDataToParseError as err:
            return [err.msg]


class card(plugin.plugin):
    """Plugin's commands."""

    def __init__(self, bot):
        super().__init__(bot)

    @command
    @doc('card <cardname>: show card description of <cardname>')
    def card(self, sender_nick, args, **kwargs):
        card = Card(args)
        for line in card.formatted:
            self.bot.say(line)
