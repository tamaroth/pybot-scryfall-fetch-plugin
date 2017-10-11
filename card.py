from plugin import *
from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.error import URLError
from json import loads

class card(plugin):
    def __init__(self, bot):
        super().__init__(bot)

    @command
    @doc('card <cardname>: show card description of <cardname>')
    def card(self, sender_nick, args, **kwargs):
        if not args: return
        for line in ScryFall.get_card(args):
            self.bot.say(line)


class ScryFall:
    @classmethod
    def get_card(cls, card_name):
        cls.error = ''
        text = cls.__fetch_card_details(card_name)
        if not text:
            text.append(cls.error)
        return text

    @classmethod
    def __fetch_card_details(cls, card_name):
        possible_cards = {}
        text = []
        cards = cls.__fetch_card_data(f'https://api.scryfall.com/cards/search?q={"+".join(card_name)}')
        if not cards:
            return text

        for card_info in cards:
            name = card_info['name']
            uri = card_info['prints_search_uri']
            if name.lower() == ' '.join(card_name).lower():
                return cls.__get_card_text_from_uri(uri)
            possible_cards[name] = uri

        if len(possible_cards) == 1:
            name, uri = possible_cards.popitem()
            return cls.__get_card_text_from_uri(uri)

        text = ['Possible cards: ', '|'.join(possible_cards)]
        return text

    @classmethod
    def __get_card_text_from_uri(cls, uri):
        return CardParser.get_card_text(cls.__fetch_card_data(uri))

    @classmethod
    def __fetch_card_data(cls, uri):
        try:
            with urlopen(uri) as response:
                return loads(response.read().decode('utf-8'))['data']
        except URLError:
            cls.error = 'Couldn\'t find the card!'
            return []
        except HTTPError:
            cls.error = 'Couldn\'t find the card!'
            return []


class CardParser:
    @classmethod
    def get_card_text(cls, card_data):
        cls.card_data = card_data
        lines = []
        if len(cls.card_data) > 0:
            cls.card_info = cls.card_data[0]
            lines = [f'{cls.__get_name()} {cls.__get_cost()} |{cls.__get_type()}|{cls.__get_pt()} - {cls.__get_rarity()}']
            lines += cls.__get_oracle()
            lines.append(cls.__get_sets())
        return lines

    @classmethod
    def __decorate_mana_cost(cls, text):
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

    @classmethod
    def __get_rarity(cls):
        rarity = {
            'common': f'{color.black("common")}',
            'uncommon': f'{color.light_grey("uncommon")}',
            'rare': f'{color.blue("rare")}',
            'mythic': f'{color.orange("mythic")}'
        }
        for key, value in rarity.items():
            if key == cls.card_info['rarity']:
                return value
        return 'unknown rarity!'

    @classmethod
    def __get_name(cls):
        return f'{color.purple(cls.card_info["name"])}'

    @classmethod
    def __get_cost(cls):
        return f'{cls.__decorate_mana_cost(cls.card_info["mana_cost"])}'

    @classmethod
    def __get_type(cls):
        return f'{cls.card_info["type_line"]}'

    @classmethod
    def __get_oracle(cls):
        try:
            return cls.__decorate_mana_cost(cls.card_info['oracle_text']).split('\n')
        except KeyError:
            return []

    @classmethod
    def __get_pt(cls):
        try:
           p = cls.card_info['power']
           t = cls.card_info['toughness']
           return f'{p}/{t}'
        except KeyError:
           return ''

    @classmethod 
    def __get_sets(cls):
        try:
            sets = 'Available sets:'
            for card in cls.card_data:
                sets += f' {card["set"].upper()}'
            return sets
        except KeyError:
            return ''
