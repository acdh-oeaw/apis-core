import importlib
import inspect
from django.contrib.contenttypes.models import ContentType
from django.db.models.base import ModelBase


class GetContentTypes:


    # class memeber dictionary, used for caching ContentType objects in method get_content_type_of_class_or_instance
    class_content_type_dict = {}


    def get_names(self):
        """Function to create Module/Class name tuples

        Returns:
            [list]: [list of Modile/Class tuples]
        """            
        res = []
        for cls in self._lst_cont:
            res.append((cls.__module__.split('.')[-2], cls.__name__))
        return res

    def get_model_classes(self):
        """Returns list of django model classes

        Returns:
            [list]: [django model classes]
        """            
        return self._lst_cont


    @classmethod
    def get_content_type_of_class_or_instance(cls, model_class_or_instance):
        """
        Helper method which caches ContentType of a given model class or instance. When first called on a model
        it fetches its respective ContentType from DB and caches it in a class dictionary. Later this dictionary is
        called

        :param model_class_or_instance: can be either a model class or an instance of a model class
        :return: The django ContentType object for the given parameter
        """

        model_class = None
        if type(model_class_or_instance) is ModelBase:
            # true if model_class_or_instance is model class
            model_class = model_class_or_instance
        elif type(type(model_class_or_instance)) is ModelBase:
            # true if model_class_or_instance is model instance
            model_class = type(model_class_or_instance)
        else:
            raise Exception(
                f"Passed argument is neither model class nor model instance: {type(model_class_or_instance)}"
            )

        if model_class not in cls.class_content_type_dict:
            cls.class_content_type_dict[model_class] = ContentType.objects.get(model=model_class.__name__)
        return cls.class_content_type_dict[model_class]


    def __init__(self, lst_conts=None):
        """

        Args:
            lst_conts ([list], optional): [list of entity names]. Defaults to list of apis_core entities.
        """        
        models_exclude = ["texttype_collections", "relationbaseclass", "baserelationmanager", "relationpublishedqueryset"]
        apis_modules = ['apis_core.apis_metainfo.models', 'apis_core.apis_vocabularies.models', 'apis_core.apis_entities.models', 'apis_core.apis_relations.models']
        if lst_conts is not None:
            r2 = []
            for c in lst_conts:
                for c2 in apis_modules:
                    if c in c2:
                        r2.append(c2)
            apis_modules = r2
        lst_cont_pre = [importlib.import_module(x) for x in apis_modules]
        lst_cont = []
        for m in lst_cont_pre:
            for cls_n in dir(m):
                if not cls_n.startswith('__') and "__module__" in list(dir(getattr(m, cls_n))):
                    if getattr(m, cls_n).__module__ in apis_modules and cls_n.lower() not in models_exclude and not "abstract" in cls_n.lower() and inspect.isclass(getattr(m, cls_n)):
                        lst_cont.append(getattr(m, cls_n))
        self._lst_cont = lst_cont