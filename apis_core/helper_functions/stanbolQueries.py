import requests
import json
from apis_core.default_settings.NER_settings import StbGeoQuerySettings, autocomp_settings


def decide_score_stanbol(results, dec_diff):
    if type(results) == dict:
        return results
    if len(results) == 1:
        return results[0]
    res2 = [(r['http://stanbol.apache.org/ontology/entityhub/query#score'][0]['value'], r) for r in results]
    res2.sort(key=lambda tup: tup[0], reverse=True)
    if res2[0][0] > res2[1][0] + dec_diff:
        return res2[0][1]
    else:
        return False


def find_geonames2(ca, name, adm=None, **kwargs):
    headers = {'Content-Type': 'application/json'}
    ca_feature = ca.stored_feature
    if not ca_feature:
        return False
    if adm:
        ca_data = ca.get_data(name, adm)
    else:
        ca_data = ca.get_data(name)
    ca.get_next_feature()
    r = requests.post(ca_feature['URL'], data=json.dumps(ca_data), headers=headers)
    if r.status_code == 200:
        res = r.json()
        if len(res['results']) == 1:
            return True, res['results'][0]
        elif len(res['results']) > 0:
            dec = decide_score_stanbol(res['results'], kwargs['dec_diff'])
            if dec:
                return True, dec
            else:
                return False, res['results']
        else:
            return False, False
    else:
        print(r.content)


def find_loc(lst, geonames_chains=False, dec_diff=5):
    prev_elem = False
    t = False
    if not geonames_chains:
        geonames_chains = []
        for c in autocomp_settings['Place']:
            geonames_chains.append(c['url'])
    if len(lst) == 1:
        pl_selected_fields = StbGeoQuerySettings('place').selected
        headers = {'Content-Type': 'application/json'}
        results = []
        for s in geonames_chains:
            ldpath = ""
            for d in pl_selected_fields:
                ldpath += "{} = <{}>;\n".format(d.split('#')[-1], d)
            data = {
                'limit': 20,
                'name': lst[0],
                'ldpath': ldpath
            }
            r = requests.get(s, params=data, headers=headers)
            if r.status_code == 200:
                res = r.json()
                if len(res['results']) > 0:
                    results.extend(res['results'])
        if len(results) > 1:
            test = decide_score_stanbol(results, dec_diff=dec_diff)
            if test:
                return True, test
            else:
                return False, results
        elif len(results) == 1:
            return True, results
        else:
            return False, False
    elif len(lst) > 1:
        for ind, c in enumerate(lst):
            if ind < len(lst)-1:
                if not t:
                    t = StbGeoQuerySettings('admin')
                if prev_elem:
                    countr = find_geonames2(t, c, prev_elem, dec_diff=dec_diff)
                else:
                    countr = find_geonames2(t, c, dec_diff=dec_diff)
                check = True
                while check:
                    if countr:
                        if countr[0]:
                            if countr[1]['http://www.geonames.org/ontology#featureCode'][0]['value'] == 'http://www.geonames.org/ontology#A.PCLI':
                                prev_elem = (
                                    countr[1]['id'],
                                    'http://www.geonames.org/ontology#parentCountry'
                                )
                            else:
                                prev_elem = (countr[1]['id'], 'http://www.geonames.org/ontology#parent'+countr[1]['http://www.geonames.org/ontology#featureCode'][0]['value'].split('.')[-1])
                            check = False
                        if not countr[0]:
                            check = False
                    else:
                        check = False
            else:
                o = StbGeoQuerySettings('place')
                if prev_elem:
                    place = find_geonames2(o, c, prev_elem, dec_diff=dec_diff)
                else:
                    place = find_geonames2(o, c, dec_diff=dec_diff)
                while place:
                    if place[1]:
                        return place
                    else:
                        if prev_elem:
                            place = find_geonames2(o, c, prev_elem, dec_diff=dec_diff)
                        else:
                            place = find_geonames2(o, c, dec_diff=dec_diff)
                return False


def retrieve_obj(uri):
    headers = {'Content-Type': 'application/json'}
    r = requests.get(
        'http://enrich.acdh.oeaw.ac.at/entityhub/site/geoNames_S_P_A/entity',
        params={'id': uri}, headers=headers
    )
    if r.status_code == 200:
        return r.json()
    else:
        return False


def query_geonames_chains(q, chains=['http://enrich.acdh.oeaw.ac.at/entityhub/site/geoNames_S_P_A/find'],
                          rest_feature=['A', 'P'], dec_diff=5):
    results = []
    ids = []
    headers = {'Content-Type': 'application/json'}
    for chain in chains:
        data = {'limit': 100, 'name': q,
                'ldpath': """name = <http://www.geonames.org/ontology#name>;
                \nfeatureClass = <http://www.geonames.org/ontology#featureClass>;\n
                featureCode = <http://www.geonames.org/ontology#featureCode>;\n"""}
        r = requests.get(chain, params=data, headers=headers)
        res = r.json()
        for t in res['results']:
            if t['id'] not in ids and t['featureClass'][0]['value'].split('#')[1] in rest_feature:
                results.append(t)
                ids.append(t['id'])
    if len(results) > 0:
        dec_st = decide_score_stanbol(results, dec_diff)
        if dec_st:
            return True, dec_st
        else:
            return False, results
    else:
        return False, False
