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
        for line in MtgCard().get_card(args):
            self.bot.say(line)

class MtgCard:
    def fetch_card_data(self, uri):
        try:
            with urlopen(uri) as response:
                return loads(response.read().decode('utf-8'))['data']
        except URLError:
            self.error = 'Couldn\'t find the card!'
            return []
        except HTTPError:
            self.error = 'Couldn\'t find the card!'
            return []

    def decorate_mana_cost(self, str):
        colours = {
            '{W}': f'{color.yellow("{W}")}',
            '{U}': f'{color.blue("{U}")}',
            '{R}': f'{color.red("{R}")}',
            '{B}': f'{color.black("{B}")}',
            '{G}': f'{color.green("{G}")}'
        }
        for key, value in colours.items():
            str = str.replace(key, value)
        return str

    def get_name(self):
        return f'{color.white(self.card_info["name"])}'

    def get_cost(self):
        return f'{self.decorate_mana_cost(self.card_info["mana_cost"])}'

    def get_type(self):
        return f'{self.decorate_mana_cost(self.card_info["type_line"])}'

    def get_oracle(self):
        try:
            return self.card_info['oracle_text'].split('\n')
        except KeyError:
            return []

    def get_pt(self):
        try:
           p = self.card_info['power']
           t = self.card_info['toughness']
           return f'{p}/{t}'
        except KeyError:
           return ''

    def get_sets(self):
        try:
            sets = 'Available sets:'
            for card in self.card_data:
                sets += f' {card["set"].upper()}'
            return sets
        except KeyError:
            return ''

    def get_card_text(self):
        lines = []
        if len(self.card_data) > 0:
            self.card_info = self.card_data[0]
            lines = [f'{self.get_name()} {self.get_cost()} |{self.get_type()}|{self.get_pt()}']
            lines += self.get_oracle()
            lines.append(self.get_sets())
        return lines

    def get_card_text_from_uri(self, uri):
        self.card_data = self.fetch_card_data(uri)
        return self.get_card_text()

    def fetch_card_details(self, card_name):
        possible_cards = {}
        text = []
        cards = self.fetch_card_data(f'https://api.scryfall.com/cards/search?q={"+".join(card_name)}')
        if not cards:
            return text

        for card_info in cards:
            name = card_info['name']
            uri = card_info['prints_search_uri']
            if name.lower() == card_name:
                return self.get_card_text_from_uri(uri)
            possible_cards[name] = uri

        if len(possible_cards) == 1:
            name, uri = possible_cards.popitem()
            return self.get_card_text_from_uri(uri)

        text = ['Possible cards: ', '|'.join(possible_cards)]
        return text

    def get_card(self, card_name):
        self.error = ''
        text = self.fetch_card_details(card_name)
        if not text:
            text.append(self.error)
        return text
