from SPARQLWrapper import SPARQLWrapper, JSON
from urllib.parse import urlsplit


class sparql_coin_autocomplete(object):
    def query(self, q, page_size=20, offset=0):

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
        sparql = SPARQLWrapper(self.url)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        res = []
        for r in results['results']['bindings']:
            txt = '''<span class="apis-autocomplete-span coin" data-vis-tooltip="coin"
             data-apis-pic="{}"><small>nom</small>&nbsp;<b>{}</b>&nbsp;({})</span>
                    '''.format(r['pic']['value'], r['name']['value'], urlsplit(r['o']['value']).netloc)
            res.append({'text': txt, 'id': 'nomisma::'+r['id']['value']})
        self.result = res
        return res

    def __init__(self):
        self.url = "http://nomisma.org/query"
        self.key = "nomisma"
