

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
        func_list = {}
        if entity not in func_list.keys():
            self.results = None
            return None
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
