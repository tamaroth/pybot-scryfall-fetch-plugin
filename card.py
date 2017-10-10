import json

from plugin import *
from urllib import request

class card(plugin):
    def __init__(self, bot):
        super().__init__(bot)

    @command
    @doc('test <cardname>: show card description of <cardname>')
    def card(self, sender_nick, args, **kwargs):
        if not args: return
        card = ''.join(args)
        url = 'https://api.scryfall.com/cards/named?fuzzy=' + '+'.join(args)  + '&format=json'
        result = ''
        with request.urlopen(url) as response:
            result = response.read().decode('utf-8')
        j = json.loads(result)
        card = MtgCard(j)
        for line in card.text:
            self.bot.say(line)

class MtgCard(object):
    def decorate_mana_cost(self, str):
        str = str.replace('{W}', f'{color.white("{W}")}')
        str = str.replace('{U}', f'{color.blue("{U}")}')
        str = str.replace('{R}', f'{color.red("{R}")}')
        str = str.replace('{B}', f'{color.black("{B}")}')
        str = str.replace('{G}', f'{color.green("{G}")}')
        return str

    def get_name(self):
        return f'{color.white(self.j["name"])}'

    def get_cost(self):
        return f'{decorate_mana_cost(self.j["mana_cost"])}'

    def get_type(self):
        return decorate_mana_cost(self.j['type_line']) 

    def get_oracle(self):
        try:
            return self.j['oracle_text'].split('\n')
        except KeyError:
            return []

    def get_pt(self):
        try:
           p = self.j['power']
           t = self.j['toughness']
           return f'{p}/{t}'
        except KeyError:
           return ''

    def value(self):
        card = []
        card.append(f'{self.get_name()} {self.get_cost()} |{self.get_type()}| {self.get_pt()}')
        card += self.get_oracle()
        return card

    def __init__(self, source):
        self.j = source
        self.text = self. value()
