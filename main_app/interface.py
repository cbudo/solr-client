import pysolr
import pandas as pd
import numpy as np
import nltk

# nltk.download()

"""
# Setup a Solr instance. The timeout is optional.
solr = pysolr.Solr('http://solr.csse.rose-hulman.edu:8983/solr/beerbase', timeout=10)

# How you'd index data.
solr.add([
    {
        "name": "MadTree",
        "location": "Cincinnati",
        "keywords": ["Craft"]
    },
    {
        "name": "Rubus Cacao",
        "brewery": "MadTree",
        "style": "Chocolate Stout",
        "ibu": 9000,
        "abv": 54.8,
        "keywords": ["Craft"]
    }
])

filter_queries = []
results = solr.search('MadTree', fq=filter_queries, rows=100)

print("Saw {0} result(s).".format(len(results)))

breweries_df = pd.read_csv('./csvs/breweries.csv')
breweries_geocode_df = pd.read_csv('./csvs/breweries_geocode.csv')
categories_df = pd.read_csv('./csvs/categories.csv')
styles_df = pd.read_csv('./csvs/styles.csv')

better_beers_df = beers_df[:5]
print(better_beers_df.T)

print(breweries_df[:5].T)

print(breweries_geocode_df[:5].T)

print(categories_df[:5].T)

print(styles_df[:5].T)
"""


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
    def __init__(self, bid, name, city, state, country, description):
        self.id = bid
        self.name = name
        self.city = city
        self.state = state
        self.country = country
        self.keywords = _process_description(description)


class Category:
    def __init__(self, cid, name):
        self.id = cid
        self.name = name


class Style:
    def __init__(self, sid, name):
        self.id = sid
        self.name = name


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


def _load_beers():
    beers_df = pd.read_csv('./csvs/beers.csv')
    for beer in beers_df.iterrows():
        actual_data = beer[1]
        name = str(actual_data['name'])
        description = str(actual_data['descript'])
        try:
            bid = int(actual_data['id'])
            brid = int(actual_data['brewery_id'])
            cid = int(actual_data['cat_id'])
            sid = int(actual_data['style_id'])
            abv = float(actual_data['abv'])
            ibu = int(actual_data['ibu'])
        except ValueError as e:
            print("Could not parse info for:", name)
            continue

        new_beer = Beer(bid, brid, name, cid, sid, abv, ibu, description)

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

    for included_beer in beer_brew_dict[15]:
        print(included_beer.name)

beer_dict = {}
beer_brew_dict = {}
beer_cat_dict = {}
beer_style_dict = {}

if __name__ == "__main__":
    _load_beers()
