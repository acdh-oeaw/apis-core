from django.db import models

def generate_all_fields():
    """
    This function goes through every entity, relation, and relationtype model and automatically wires them together
    by setting ManyToMany fields to each other through the relation model. This way the relations of a given entity
    to any other entity or relationtype can be queried much more directly and without the overhead of going through
    the relation model each time.

    The wiring is done by going reflectively through the python code and finding in the respective model modules the relevant classes.

    Django's ContentType interface could not be used since this relies on full class declaration before calling any models,
    however since we want to define attributes of models during their declaration, this was not possible and thus python's
    own code inspection had to be used.

    E.g. for Person these fields are auto-generated: event_set, institution_set, personB_set, personA_set, place_set, work_set
    And each of those fields are ManyToMany Managers where their django methods can be used upon, such as all() and filter()

    E.g. for PersonWork these fields are auto-generated: related_person, and related_work.
    for PersonPerson: related_personA, and related_personB

    :return: None
    """

    # TODO __sresch__ : check for best practice on local imports vs circularity problems.
    from apis_core.apis_entities.models import AbstractEntity
    from apis_core.apis_relations.models import AbstractRelation
    from apis_core.apis_vocabularies.models import AbstractRelationType



    def create_function_get_related_entity_class(related_entity_class):
        """
        :param related_entity_class: the class which the generated class method shall return
        :return: an anonymous function which is assigned as method with a label respective to relation and entity classes.
        """
        return classmethod(lambda cls: related_entity_class)

    def create_function_get_related_entity_field_name(related_entity_field_name):
        """
        :param related_entity_field_name: the name of the related entity which the generated class method shall return
        :return: an anonymous function which is assigned as method with a label respective to relation and entity classes.
        """
        return classmethod(lambda cls: related_entity_field_name)




    def pair_up_relations_relationtypes(relation_classes, relationtype_classes):
        """
        helper function to pair up the relation and relationtype classes so that potential mismatches between them are
        detected early on.

        :param relation_classes: classes of all relations from the module apis_relations/models.py
        :param relationtype_classes: classes of all relationtypes from the module apis_vocabularies/models.py
        :return: list of tuples between relations and their respective relationtype classes
        """

        # result list
        rc_rtc_pairs = []

        # helper set, where initially all the classes are inserted, and only removed if a pairing was found
        no_pairing_found = set(relation_classes + relationtype_classes)

        # Iterate over all relation and relationtype classes
        for rc in relation_classes:
            for rtc in relationtype_classes:

                # compare their name, to check if they should be regarded as pair (This depends on the APIS design
                # decision that given a relation class its respective relationtype must be named the same but with a
                # 'Relation' added at the end)
                if rc.__name__ in rtc.__name__:
                    rc_rtc_pairs.append((rc, rtc))
                    no_pairing_found.remove(rc)
                    no_pairing_found.remove(rtc)
                    break

        # Check if any classes are left without any pairing found
        if len(no_pairing_found) > 0:

            message = ""
            for cls in no_pairing_found:
                message += "Found no corresponding Relation or RelationType class to: \n" + str(cls) + "!"

            raise Exception(message)

        return rc_rtc_pairs


    # all relation, relationtype classes to be iterated over:
    relation_relationtype_pairs = pair_up_relations_relationtypes(
        relation_classes=AbstractRelation.get_all_relation_classes(),
        relationtype_classes=AbstractRelationType.get_all_relationtype_classes()
    )
    # all entity classes to be iterated over:
    entity_classes = AbstractEntity.get_all_entity_classes()


    # Iterate over all entity classes, twice, so that all relations between all entity classes are covered.
    for entity_class_a in entity_classes:
        for entity_class_b in entity_classes:

            entity_class_name_a = entity_class_a.__name__.lower()
            entity_class_name_b = entity_class_b.__name__.lower()

            # inner loop iterating over each of the relation_class and relationtype at the same time
            for relation_class, relationtype_class in relation_relationtype_pairs:


                # Check if current relation related to both entities
                # Note that this way two entites are checked twice, such as person-place and place-person
                # but however in the relation model only one of these two exists. Thus the right one will be picked.
                if entity_class_name_a + entity_class_name_b == relation_class.__name__.lower():

                    if entity_class_a != entity_class_b:



                        # On relation models: generate fields from relation to entity and from relation to relationtype
                        ################################################################################################

                        relation_field_name_a = "related_" + entity_class_name_a
                        relation_field_name_b = "related_" + entity_class_name_b

                        # To stick to common Django ORM Syntax, set the field name in the related entity class to
                        # the current relation name and add '_set' to it (since going from the entity one would have
                        # multiple relation instances possibly.)
                        relation_field_name_in_other_class = entity_class_name_a + entity_class_name_b + "_set"

                        # Create the related entity field A.
                        models.ForeignKey(
                            to=entity_class_a,
                            blank=True,
                            null=True,
                            on_delete=models.CASCADE,
                            related_name=relation_field_name_in_other_class
                        ).contribute_to_class(relation_class, relation_field_name_a)

                        # Create the related entity field B.
                        models.ForeignKey(
                            to=entity_class_b,
                            blank=True,
                            null=True,
                            on_delete=models.CASCADE,
                            related_name=relation_field_name_in_other_class
                        ).contribute_to_class(relation_class, relation_field_name_b)

                        # Create the related relationtype field
                        models.ForeignKey(
                            to=relationtype_class,
                            blank=True,
                            null=True,
                            on_delete=models.CASCADE,
                            related_name=relation_field_name_in_other_class
                        ).contribute_to_class(relation_class, "relation_type")

                        # Implemented the following methods programmatically by setting the respective relations,
                        # entity class references, names, etc.
                        # Note that these methods are first defined as stumps within AbstractRelation for documentation
                        # purposes.

                        relation_class.get_related_entity_classA = \
                            create_function_get_related_entity_class(entity_class_a)

                        relation_class.get_related_entity_classB = \
                            create_function_get_related_entity_class(entity_class_b)

                        relation_class.get_related_entity_field_nameA = \
                            create_function_get_related_entity_field_name(relation_field_name_a)

                        relation_class.get_related_entity_field_nameB = \
                            create_function_get_related_entity_field_name(relation_field_name_b)

                        relation_class.add_relation_class_of_entity_class(entity_class_a)
                        relation_class.add_relation_class_of_entity_class(entity_class_b)
                        relation_class.add_relation_field_name_of_entity_class(
                            relation_name=relation_field_name_in_other_class, entity_class=entity_class_a)
                        relation_class.add_relation_field_name_of_entity_class(
                            relation_name=relation_field_name_in_other_class, entity_class=entity_class_b)



                        # On entity models: generate fields from entity to entity and from entity to relationtype
                        ################################################################################################

                        field_name_to_entity_a = entity_class_name_a + "_set"
                        field_name_to_entity_b = entity_class_name_b + "_set"
                        field_name_to_entity_b_relationtype = entity_class_name_b + "_relationtype_set"
                        field_name_to_entity_a_relationtype = entity_class_name_a + "_relationtype_set"

                        # Add those names already into the respective class's list of field names
                        entity_class_a.add_related_entity_field_name(field_name_to_entity_b)
                        entity_class_b.add_related_entity_field_name(field_name_to_entity_a)
                        entity_class_a.add_related_relationtype_field_name(field_name_to_entity_b_relationtype)
                        entity_class_b.add_related_relationtype_field_name(field_name_to_entity_a_relationtype)
                        relationtype_class.add_related_entity_field_name(field_name_to_entity_b)
                        relationtype_class.add_related_entity_field_name(field_name_to_entity_a)

                        # entity A to entity B, and B back to A
                        models.ManyToManyField(
                            to=entity_class_b,
                            through=relation_class,
                            related_name=field_name_to_entity_a,
                            blank=True,
                        ).contribute_to_class(entity_class_a, field_name_to_entity_b)

                        # entity A to RelationType via entity B, and RelationType back to A
                        models.ManyToManyField(
                            to=relationtype_class,
                            through=relation_class,
                            related_name=field_name_to_entity_a,
                            blank=True,
                        ).contribute_to_class(entity_class_a, field_name_to_entity_b_relationtype)

                        # entity B to RelationType via entity A, and RelationType back to B
                        models.ManyToManyField(
                            to=relationtype_class,
                            through=relation_class,
                            related_name=field_name_to_entity_b,
                            blank=True,
                        ).contribute_to_class(entity_class_b, field_name_to_entity_a_relationtype)



                    else:



                        # On relation models: generate fields from relation to entity and from relation to relationtype
                        ################################################################################################

                        # now that both entity classes are the same, just take the values from the class 'a'
                        entity_class_name = entity_class_name_a
                        entity_class = entity_class_a


                        relation_field_name_a = "related_" + entity_class_name + "A"
                        relation_field_name_b = "related_" + entity_class_name + "B"

                        # Within APIS it was manually set that from a given entity which relates to a relation containing
                        # the same entity class twice (e.g. PersonPerson), within the given entity class the
                        # field's name was 'related_<entity>A', and 'related_<entity>B' (e.g. Person.related_personA).
                        # This is not consistent with the other relation fields of a given entity
                        # (e.g. for PersonWork, in Person and Work, it would refer to the relation via 'personwork_set').
                        #
                        # This should be changed, but it would result in crashes where code would not be adapted.
                        #
                        # So, for now, in order to not break APIS and to keep downwards-compatibility, the same fields are
                        # generated as before.
                        relation_field_name_in_other_class_a = relation_field_name_b
                        relation_field_name_in_other_class_b = relation_field_name_a
                        relation_field_name_in_other_class = entity_class_name_a + entity_class_name_b + "_set"

                        # TODO __sresch__ : use the following related name for consistency reasons once most code breaking parts due to this change are identified.
                        #
                        # Unfortuantely it does not seem possible to have an Entity refer to a symmetric relation with
                        # only the relation name (E.g. that both Person A and Person B would refer to the PersonPerson relation
                        # via 'personperson_set'). So later it will be changed to 'personpersonA_set', and 'personpersonB_set'
                        # to be a bit more consistent with other usages. So, uncomment the following once breaking parts
                        # are identified and prepared for it.
                        #
                        # relation_field_name_from_entity_a = entity_class_name * 2 + "B_set"
                        # relation_field_name_from_entity_b = entity_class_name * 2 + "A_set"

                        # Create the related entity field A.
                        models.ForeignKey(
                            to=entity_class,
                            blank=True,
                            null=True,
                            on_delete=models.CASCADE,
                            related_name=relation_field_name_in_other_class_a
                        ).contribute_to_class(relation_class, relation_field_name_a)

                        # Create the related entity field B.
                        models.ForeignKey(
                            to=entity_class,
                            blank=True,
                            null=True,
                            on_delete=models.CASCADE,
                            related_name=relation_field_name_in_other_class_b
                        ).contribute_to_class(relation_class, relation_field_name_b)

                        # Create the related relaiontype field
                        models.ForeignKey(
                            to=relationtype_class,
                            blank=True,
                            null=True,
                            on_delete=models.CASCADE,
                            related_name=relation_field_name_in_other_class
                        ).contribute_to_class(relation_class, "relation_type")

                        # Implemented the following methods programmatically by setting the respective relations,
                        # entity class references, names, etc.
                        # Note that these methods are first defined as stumps within AbstractRelation for documentation
                        # purposes.

                        relation_class.get_related_entity_classA = \
                            create_function_get_related_entity_class(entity_class)

                        relation_class.get_related_entity_classB = \
                            create_function_get_related_entity_class(entity_class)

                        relation_class.get_related_entity_field_nameA = \
                            create_function_get_related_entity_field_name(relation_field_name_a)

                        relation_class.get_related_entity_field_nameB = \
                            create_function_get_related_entity_field_name(relation_field_name_b)

                        relation_class.add_relation_class_of_entity_class(entity_class)
                        relation_class.add_relation_field_name_of_entity_class(
                            relation_name=relation_field_name_in_other_class_a, entity_class=entity_class)
                        relation_class.add_relation_field_name_of_entity_class(
                            relation_name=relation_field_name_in_other_class_b, entity_class=entity_class)



                        # On entity models: generate fields from entity to entity and from entity to relationtype
                        ################################################################################################

                        # Define all the names for the ManyToMany fields generated below
                        field_name_to_entity_a = entity_class_name_a + "A_set"
                        field_name_to_entity_b = entity_class_name_b + "B_set"
                        field_name_to_entity_b_relationtype = entity_class_name_b + "B_relationtype_set"
                        field_name_to_entity_a_relationtype = entity_class_name_a + "A_relationtype_set"

                        # Add those names already into the respective class's list of field names
                        entity_class_a.add_related_entity_field_name(field_name_to_entity_b)
                        entity_class_b.add_related_entity_field_name(field_name_to_entity_a)
                        entity_class_a.add_related_relationtype_field_name(field_name_to_entity_b_relationtype)
                        entity_class_b.add_related_relationtype_field_name(field_name_to_entity_a_relationtype)
                        relationtype_class.add_related_entity_field_name(field_name_to_entity_b)
                        relationtype_class.add_related_entity_field_name(field_name_to_entity_a)

                        # entity A to same entity B, and B back to A
                        models.ManyToManyField(
                            to=entity_class_b,
                            through=relation_class,
                            related_name=field_name_to_entity_a,
                            blank=True,
                            symmetrical=False,
                            through_fields=("related_" + entity_class_name_a + "A", "related_" + entity_class_name_b + "B")
                        ).contribute_to_class(entity_class_a, field_name_to_entity_b)

                        # entity A to RelationType via entity B, and RelationType back to A
                        models.ManyToManyField(
                            to=relationtype_class,
                            through=relation_class,
                            related_name=field_name_to_entity_a,
                            blank=True,
                            symmetrical=False,
                            through_fields=("related_" + entity_class_name_a + "A", "relation_type")
                        ).contribute_to_class(entity_class_a, field_name_to_entity_b_relationtype)

                        # entity B to RelationType via entity A, and RelationType back to B
                        models.ManyToManyField(
                            to=entity_class_b,
                            through=relation_class,
                            related_name=field_name_to_entity_a_relationtype,
                            blank=True,
                            symmetrical=False,
                            through_fields=("relation_type", "related_" + entity_class_name_b + "B")
                        ).contribute_to_class(relationtype_class, field_name_to_entity_b)



                    # if entity_class_a_name + entity_class_b_name == relation_class.__name__.lower()
                    # equals to True, then for entity_class_a and entity_class_b, their respective relation class
                    # has been found, thus interrupt the loop going through these relation classes.
                    break
