import requests
import json
from apis.settings.NER_settings import StbGeoQuerySettings, autocomp_settings


def decide_score_stanbol(results, dec_diff):
    difference = dec_diff
    val1 = results[0]['http://stanbol.apache.org/ontology/entityhub/query#score'][0]['value']
    val2 = results[1]['http://stanbol.apache.org/ontology/entityhub/query#score'][0]['value']
    if val1 > val2+difference:
        return results[0]
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


def find_loc(lst, dec_diff=5):
    prev_elem = False
    t = False
    if len(lst) == 1:
        pl_selected_fields = StbGeoQuerySettings('place').selected
        headers = {'Content-Type': 'application/json'}
        results = []
        for s in autocomp_settings['Place']:
            ldpath = ""
            for d in pl_selected_fields:
                ldpath += "{} = <{}>;\n".format(d.split('#')[-1], d)
            data = {
                'limit': 20,
                'name': lst[0],
                'ldpath': ldpath
            }
            r = requests.get(s['url'], params=data, headers=headers)
            if r.status_code == 200:
                res = r.json()
                if len(res['results']) > 0:
                    results.extend(res['results'])
        if len(results) > 1:
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
