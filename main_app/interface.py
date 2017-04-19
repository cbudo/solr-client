import pysolr
import pandas as pd
import numpy as np
import nltk

nltk.download()

beer_dict = {}
beer_brew_dict = {}
beer_cat_dict = {}
beer_style_dict = {}
brewery_dict = {}
style_dict = {}
style_category_dict = {}
category_dict = {}


def _process_description(description):
    description = str(description)
    description.split(' ')
    tokens = nltk.word_tokenize(description)
    tagged = nltk.pos_tag(tokens)
    accepted_words = []
    for word in tagged:
        if (word[1][0] == 'N') or (word[1] == 'FW'):
            accepted_words.append(word[0])
    return accepted_words


class Brewery:
    def __init__(self, bid, name, city, state, country, phone, website):
        self.id = bid
        self.name = name
        self.city = city
        self.state = state
        self.country = country
        self.phone = phone
        self.website = website

    def get_repr(self):
        return {
            "name": self.name,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "keywords": [self.name, self.city, self.state, self.country,
                         self.website, self.phone]
        }


class Category:
    def __init__(self, cid, name):
        self.id = cid
        self.name = name


class Style:
    def __init__(self, sid, cid, name):
        self.id = sid
        self.cid = cid
        self.name = name
        self.category = ''


class Beer:
    def __init__(self, bid, brid, name, cid, sid, abv, ibu, description):
        self.bid = bid
        self.name = name
        self.brid = brid
        self.brewery = ''
        self.cid = cid
        self.category = ''
        self.sid = sid
        self.style = ''
        self.abv = abv
        self.ibu = ibu
        self.keywords = _process_description(description)

    def get_repr(self):
        return {
            "name": self.name,
            "brewery": self.brewery,
            "category": self.category,
            "style": self.style,
            "abv": self.abv,
            "ibu": self.ibu,
            "keywords": self.keywords
        }


def _load_beers():
    beers_df = pd.read_csv('./csvs/beers.csv')
    for curr_beer in beers_df.iterrows():
        actual_data = curr_beer[1]
        name = str(actual_data['name'])
        description = str(actual_data['descript'])
        try:
            bid = int(actual_data['id'])
            brid = int(actual_data['brewery_id'])
            cid = int(actual_data['cat_id'])
            sid = int(actual_data['style_id'])
            abv = float(actual_data['abv'])
            ibu = int(actual_data['ibu'])
        except ValueError:
            print("Could not parse info for:", name)
            continue

        new_beer = Beer(bid, brid, name, cid, sid, abv, ibu, description)

        beer_dict[new_beer.bid] = new_beer

        # Beers to Brewery Ids
        if new_beer.brid in beer_brew_dict.keys():
            beer_brew_dict[new_beer.brid].append(new_beer)

        else:
            beer_brew_dict[new_beer.brid] = [new_beer]

        # Beers to Category Ids
        if new_beer.cid in beer_cat_dict.keys():
            beer_cat_dict[new_beer.cid].append(new_beer)

        else:
            beer_cat_dict[new_beer.cid] = [new_beer]

        # Beers to Style Ids
        if new_beer.sid in beer_style_dict.keys():
            beer_style_dict[new_beer.sid].append(new_beer)

        else:
            beer_style_dict[new_beer.sid] = [new_beer]


def _load_breweries():
    breweries_df = pd.read_csv('./csvs/breweries.csv')
    for curr_brewery in breweries_df.iterrows():
        actual_data = curr_brewery[1]
        name = str(actual_data['name'])
        city = str(actual_data['city'])
        state = str(actual_data['state'])
        country = str(actual_data['country'])
        phone = str(actual_data['phone'])
        website = str(actual_data['website'])
        try:
            bid = int(actual_data['id'])
        except ValueError:
            print("Could not parse info for:", name)
            continue

        new_brewery = Brewery(bid, name, city, state, country, phone, website)
        brewery_dict[bid] = new_brewery

        if bid not in beer_brew_dict.keys():
            continue

        for included_beer in beer_brew_dict[bid]:
            included_beer.brewery = name


def _load_styles():
    styles_df = pd.read_csv('./csvs/styles.csv')
    for curr_style in styles_df.iterrows():
        actual_data = curr_style[1]
        name = str(actual_data['style_name'])
        try:
            sid = int(actual_data['id'])
            cid = int(actual_data['cat_id'])
        except ValueError:
            print("Could not parse info for:", name)
            continue

        new_style = Style(sid, cid, name)
        style_dict[sid] = new_style

        # Styles to Category Ids
        if new_style.cid in style_category_dict.keys():
            style_category_dict[new_style.cid].append(new_style)

        else:
            style_category_dict[new_style.cid] = [new_style]

        if sid not in beer_style_dict.keys():
            continue

        for included_beer in beer_style_dict[sid]:
            included_beer.style = name


def _load_categories():
    categories_df = pd.read_csv('./csvs/categories.csv')
    for category in categories_df.iterrows():
        actual_data = category[1]
        name = str(actual_data['cat_name'])
        try:
            cid = int(actual_data['id'])
        except ValueError:
            print("Could not parse info for:", name)
            continue

        new_category = Category(cid, name)
        category_dict[cid] = new_category

        if cid in style_category_dict.keys():
            for included_style in style_category_dict[cid]:
                included_style.category = name

        if cid in beer_cat_dict.keys():
            for included_beer in beer_cat_dict[cid]:
                included_beer.category = name


def _insert_into_solr():
    # Setup a Solr instance. The timeout is optional.
    solr = pysolr.Solr('http://solr.csse.rose-hulman.edu:8983/solr/beerbase/', timeout=10)

    solr.delete(q='*:*')

    print("Inserting beers...")

    all_beers = []

    for curr_beer in beer_dict.values():
        all_beers.append(curr_beer.get_repr())

    solr.add(all_beers)

    print("Inserting breweries...")

    all_breweries = []

    for curr_brewery in brewery_dict.values():

        all_breweries.append(curr_brewery.get_repr())

    solr.add(all_breweries)

    filter_queries = []
    results = solr.search('Cincinnati', fq=filter_queries, rows=100)

    print("Saw {0} result(s).".format(len(results)))


if __name__ == "__main__":
    _load_beers()
    _load_breweries()
    _load_styles()
    _load_categories()

    print("BEER CATEGORY STYLE ABV IBU KEYWORDS:")

    for beer in beer_dict.values():
        if beer.category == '':
            beer.category = 'Undefined Category'
        if beer.style == '':
            beer.style = 'Undefined Style'

        print(beer.name, beer.category, beer.style, beer.abv, beer.ibu, beer.keywords)

    print("STYLE CATEGORY:")

    for style in style_dict.values():
        if style.category == '':
            style.category = 'Undefined Category'

        print(style.name, style.category)

    print("BREWERY CITY STATE COUNTRY PHONE WEBSITE")

    for brewery in brewery_dict.values():
        print(brewery.name, brewery.city, brewery.state, brewery.country, brewery.phone, brewery.website)

    # _insert_into_solr()
