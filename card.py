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

    def __init__(self, card_json):
        if not card_json:
            raise NoDataToParseError('card_json')
        self._card = card_json

    @property
    def name(self):
        """Returns the parsed name of the card."""
        self._verify_data_key_exists('name')
        return f'{color.purple(self._card["name"])}'

    @property
    def mana_cost(self):
        """Returns the parsed cost of the card."""
        self._verify_data_key_exists('mana_cost')
        return f'{self._decorate_mana_cost(self._card["mana_cost"])}'

    @property
    def rarity(self):
        """Returns the parsed rarity of the card."""
        self._verify_data_key_exists('rarity')
        rarity = {
            'common': f'{color.black("common")}',
            'uncommon': f'{color.light_grey("uncommon")}',
            'rare': f'{color.blue("rare")}',
            'mythic': f'{color.orange("mythic")}'
        }
        for key, value in rarity.items():
            if key == self._card['rarity']:
                return value
        return 'unknown rarity!'

    @property
    def type(self):
        """Returns the parsed type of the card."""
        self._verify_data_key_exists('type_line')
        return self._card['type_line']

    @property
    def oracle_text(self):
        """Returns the parsed oracle text of the card as a list."""
        if 'oracle_text' not in self._card:
            return []
        return self._decorate_mana_cost(self._card['oracle_text']).split('\n')

    @property
    def pt(self):
        """Returns the parsed power/thoughtness of the card (if present)."""
        if not all (k in self._card for k in ('power', 'toughness')):
            return ''

        p = self._card['power']
        t = self._card['toughness']
        return f'{p}/{t}'

    @property
    def sets(self):
        """Returns the parsed list of sets in which the card is available."""
        self._verify_data_key_exists('prints_search_uri')

        sets = []
        response = Scryfall.fetch_data_as_json(self._card['prints_search_uri'])
        _verify_key_exists_in_dict('object', response)
        _verify_key_exists_in_dict('data', response)
        for card in response['data']:
            if 'set' in card:
                sets.append(card['set'].upper())

        return ','.join(sets)

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
        return text

    def _verify_data_key_exists(self, key):
        """Verifies that the data key exists in the card info."""
        _verify_key_exists_in_dict(key, self._card)


class Scryfall:
    """Fetches card information from ScryFall.com."""

    @staticmethod
    def get_card_data(card_name=None):
        """Retrieve card details from ScryFall."""
        try:
            return Scryfall.fetch_card_details(card_name)
        except NoCardError as err:
            return [err.msg]

    @staticmethod
    def fetch_card_details(card_name):
        """Fetches the text detail of the card."""

        if card_name is None:
            endpoint = '/cards/random'
        else:
            endpoint = f'/cards/search?q={"+".join(card_name)}'

        response = Scryfall.fetch_data_as_json(f'{SCRYFALL_API_ADDRESS}{endpoint}')
        if 'object' not in response:
            raise NoCardError

        object_type = response['object']

        if object_type == 'card':
            return response

        if object_type == 'list':
            if response['total_cards'] == 1:
                return response['data'][0]
            possible_cards = []
            return {
                'possible_cards': Scryfall.get_possible_cards(response, possible_cards),
                'possible_cards_count': response['total_cards'],
            }
        else:
            raise NoCardError

    @staticmethod
    def get_possible_cards(card_object, possible_cards):
        """Returns a list of possible cards from the given card list object."""
        assert card_object['object'] == 'list', 'card_object is not a list...'
        assert 'data' in card_object, 'data was not found in card object...'
        assert 'has_more' in card_object, 'has_more was not found in card object..'

        for card in card_object['data']:
            possible_cards.append(card['name'])

        if card_object['has_more'] == 'true':
            new_cards = Scryfall.fetch_data_as_json(card_object['next_page'])
            return Scryfall.get_possible_cards(new_cards, possible_cards)

        return possible_cards

    @staticmethod
    def fetch_data_as_json(uri):
        """Fetches the raw data from the URI."""
        try:
            with urllib.request.urlopen(uri) as response:
                return json.loads(response.read().decode('utf-8'))
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
            if 'possible_cards' in self._card_data:
                result = [f'Possible cards ({self._card_data["possible_cards_count"]})']
                if self._card_data['possible_cards_count'] <= 10:
                    result.append('|'.join(self._card_data['possible_cards']))
                else:
                    result.append('First 10 cards: ')
                    result.append('|'.join(self._card_data['possible_cards'][:10]))
                return result

            parser = CardParser(self._card_data)
            result = [
                f'{parser.name} {parser.mana_cost} |{parser.type}|{parser.pt} - {parser.rarity}',
            ]
            result += parser.oracle_text
            result.append(parser.sets)
            return result
        except NoDataToParseError as err:
            return [err.msg]


class card(plugin):
    """Plugin's commands."""

    def __init__(self, bot):
        super().__init__(bot)

    @command
    @doc('card <cardname>: show card description of <cardname>')
    def card(self, sender_nick, args, **kwargs):
        if not args:
            card = Card()
        else:
            card = Card(args)
        for line in card.formatted:
            self.bot.say(line)


def _verify_key_exists_in_dict(key, d):
    """Verifies that key exists in the dictionary."""
    if key not in d:
        raise NoDataToParseError(key)
