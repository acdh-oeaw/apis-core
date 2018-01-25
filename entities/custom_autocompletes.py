from SPARQLWrapper import SPARQLWrapper, JSON

def sparql_coin_autocomplete(q, page_size=20, offset=0):

    query = """
            PREFIX bio:	<http://purl.org/vocab/bio/0.1/>
            PREFIX crm:	<http://www.cidoc-crm.org/cidoc-crm/>
            PREFIX dcmitype:	<http://purl.org/dc/dcmitype/>
            PREFIX dcterms:	<http://purl.org/dc/terms/>
            PREFIX foaf:	<http://xmlns.com/foaf/0.1/>
            PREFIX geo:	<http://www.w3.org/2003/01/geo/wgs84_pos#>
            PREFIX nm:	<http://nomisma.org/id/>
            PREFIX nmo:	<http://nomisma.org/ontology#>
            PREFIX org: <http://www.w3.org/ns/org#>
            PREFIX osgeo:	<http://data.ordnancesurvey.co.uk/ontology/geometry/>
            PREFIX rdac:	<http://www.rdaregistry.info/Elements/c/>
            PREFIX skos:	<http://www.w3.org/2004/02/skos/core#>
            PREFIX spatial: <http://jena.apache.org/spatial#>
            PREFIX void:	<http://rdfs.org/ns/void#>
            PREFIX xsd:	<http://www.w3.org/2001/XMLSchema#>

            SELECT * WHERE {{
              ?o a nmo:NumismaticObject .
              ?o dcterms:title ?name .FILTER (contains(?name,"{}")) .
              ?o dcterms:identifier ?id .
              OPTIONAL {{?o foaf:thumbnail ?pic}} .
              OPTIONAL {{?o nmo:hasReverse ?rev .
                       ?rev foaf:depiction ?pic}} .
            }} LIMIT {}
            OFFSET {}""".format(q, page_size, offset*page_size)
    sparql = SPARQLWrapper("http://nomisma.org/query")
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    res = []
    for r in results['results']['bindings']:
        txt = '''<span class="autocomplete-span" data-pic="{}"><small>nom</small><b>{}</b></span>
                '''.format(r['pic']['value'], r['name']['value'])
        res.append({'text': txt, 'id': r['id']['value']})
    return res


class CustomEntityAutocompletes(object):
    """A class for collecting all the custom autocomplete functions for one entity.

    Attributes:

    - self.entity: (string) entity types
    - self.more: (boolean) if more results can be fetched (pagination)
    - self.page_size: (integer) page size
    - self.results: (list) results
    - self.query: (string) query string

    Methods:
    - self.more(): fetch more results
    """

    def __init__(self, entity, query, page_size=20, offset=0, *args, **kwargs):
        """
        :param entity: (string) entity type to fetch additional autocompletes for
        """
        func_list = {'coin': [sparql_coin_autocomplete,]}
        if entity not in func_list.keys():
            return False
        res = []
        more = dict()
        more_gen = False
        for x in func_list[entity]:
            res2 = x(query, page_size, offset)
            if len(res2) == page_size:
                more[x.__name__] = (True, offset+1)
                more_gen = True
            res.extend(res2)
        self.results = res
        self.page_size = page_size
        self.more = more_gen
        self._more_dict = more
        self.query = query
        self.offset = offset

    def get_more(self):
        """
        Function to retrieve more results.
        """
        res4 = []
        for key, value in self._more_dict.items():
            if value[0]:
                res3 = globals()[key](self.query, self.page_size, value[1])
                if len(res3) == self.page_size:
                    self._more_dict[key] = (True, value[1]+1)
                else:
                    self._more_dict[key] = (False, value[1])
                self.results.extend(res3)
                res4.extend(res3)
        return res4
