import requests


def create_qs(row, cell, q_field="dateOfBirth", char_limit=0):
    """turns the value of the cell into a lobid-querystring"""
    try:
        if len(row[cell]) > char_limit:
            qs = "{}:{} ".format(q_field, row[cell])
        else:
            qs = "{}:{}*".format(q_field, row[cell])
    except:
        qs = ""
    return qs


def lobid_qs(row, q_field='name', add_fields=[], base_url="https://lobid.org/gnd/search?q="):
    """ creates a lobid query string from the passed in fields"""
    search_url = base_url+row[q_field]+"&filter=type:Person"
    if add_fields:
        filters = []
        for x in add_fields:
            if x:
                filters.append(row[x])
        search_url = "{} AND {}".format(search_url, "AND ".join(filters))
    return search_url


def search_lobid(row, qs_field='query'):
    """ sends the value of the passed in field to lobid and returns the results in a dict """
    query = row[qs_field]
    result = {
        'query': query,
        'status': 0,
        'error': "",
        'hits': 0,
        'gnd': []
    }
    r = requests.get(query)
    try:
        r = requests.get(query)
    except requests.ConnectionError:
        result['error'] = "Connection Error"
        return result
    if r:
        if r.status_code == 200:
            result['status'] = r.status_code
            result['hits'] = r.json()['totalItems']
            if result['hits'] == 0:
                gnd = []
                print('zero hits')
            elif result['hits'] == 1:
                print("one hit")
                result['gnd'] = [r.json()['member'][0]['gndIdentifier']]
            else:
                print("{} hits".format(result['hits']))
                result['gnd'] = [x['gndIdentifier'] for x in r.json()['member']]
        else:
            result['status'] = r.status_code
    return result


# do something like below to enrich a csv with lobid

# import pandas as pd
# from pylobid import *
#
# file = "dump_from_gsheet/ASBW_persName.csv"
# df = pd.read_csv(file)
# df['dateOfBirth'] = df.apply(
#     lambda row: create_qs(row, 'Geburtsdatum', q_field="dateOfBirth", char_limit=4),
#     axis=1
# )
# df['dateOfDeath'] = df.apply(
#     lambda row: create_qs(row, 'Todesdatum', q_field="dateOfDeath", char_limit=4),
#     axis=1
# )
# df['forename'] = df.apply(
#     lambda row: create_qs(
#         row, 'Vorname', q_field="preferredNameEntityForThePerson.forename", char_limit=0
#     ),
#     axis=1
# )
# df['surname'] = df.apply(
#     lambda row: create_qs(
#         row, 'Nachname', q_field="preferredNameEntityForThePerson.surname", char_limit=0
#     ),
#     axis=1
# )
# df['query'] = df.apply(
#     lambda row: lobid_qs(row, add_fields=['forename', 'dateOfBirth', 'dateOfDeath']),
#     axis=1
# )
