from xml.sax.saxutils import escape, unescape

import lxml.etree as ET

from django.conf import settings
from django.utils.text import slugify

from .partials import TEI_NSMAP, tei_gen_header

from apis_core.apis_metainfo.models import Text
from apis_core.apis_entities.models import Person, Place, Event, Work, Institution


from collections import defaultdict

import pprint

pp = pprint.PrettyPrinter(indent=4)


def custom_escape(somestring):
    un_escaped = unescape(somestring)
    return escape(un_escaped)


# When serializing texts, we need to be able to look up
# the entity in DB to check we have all the texts (not just the
# annotated ones) — so need to map string values to classes.
# REPLACE THIS WITH LIST OF TEXTS IN ent_dict!
entity_type_string_to_class = {
    "Person": Person,
    "Place": Place,
    "Event": Event,
    "Work": Work,
    "Institution": Institution,
}

relation_type_to_tei_tag = {
    "events": "EVENT",  # What to do with this?
    "institutions": "orgName",
    "persons": "persName",
    "places": "placeName",
}


class TeiEntCreator:
    def __init__(
        self, ent_dict, base_url="entity/", include_entity_tagged_texts=False
    ):
        """
        Entry point: called from apis_core/apis_entities/api_renderers.py
        
        ent_dict is dict representing the entity

        This class is initialised, then has the serialize_full_doc method called
        on it, which in turn calls all the other methods on this class (apparently).


        """
        self.nsmap = TEI_NSMAP
        self.project = "APIS"
        s_url = getattr(settings, "APIS_BASE_URI", "http://apis.info/")
        self.base_url = f"{s_url}{base_url}"
        self.ent_dict = ent_dict
        self.ent_name = custom_escape(ent_dict.get("name", "No name provided"))
        self.ent_type = ent_dict.get("entity_type")
        self.ent_apis_id = ent_dict.get("id")
        self.gen_tei_header = tei_gen_header
        self.include_entity_tagged_texts = include_entity_tagged_texts

    def relation_groups(self):
        ent_dict = self.ent_dict
        ent_types = list(ent_dict["relations"].keys())
        self_type = "{}s".format(ent_dict["entity_type"].lower())
        relations = []
        for x in ent_types:
            group = []
            for y in ent_dict["relations"][x]:
                ent_key = list(y.keys())[2]
                rel = {}
                rel["rel_type"] = x
                rel["rel_label"] = slugify(y["relation_type"]["label"])
                if "target" in y.keys():
                    key_1 = "target"
                else:
                    key_1 = "source"
                rel["target"] = y[key_1]["id"]
                rel["target_name"] = y[key_1]["name"]
                group.append(rel)
            if group:
                relations.append(group)

        return relations

    def relation_notes(self):
        notes = []
        for group in self.relation_groups():
            note = ET.Element("{http://www.tei-c.org/ns/1.0}note")
            note_type = group[0]["rel_type"]
            note.attrib["type"] = note_type
            for item in group:
                ptr = ET.Element("ptr")
                ptr.attrib["type"] = item["rel_label"]
                ptr.attrib["target"] = "{}{}".format(self.base_url, item["target"])
                note.append(ptr)
            notes.append(note)
        return notes

    def uris_to_idnos(self):
        uris = []
        if self.ent_dict.get("uris"):
            for x in self.ent_dict.get("uris"):
                idno = ET.Element("idno")
                idno.attrib["type"] = "URL"
                if "d-nb.info" in x.get("uri"):
                    idno.attrib["subtype"] = "GND"
                idno.text = x.get("uri")
                uris.append(idno)
        return uris

    def create_work_node(self):
        work = ET.Element("{http://www.tei-c.org/ns/1.0}item")
        work.attrib["{http://www.w3.org/XML/1998/namespace}id"] = "work__{}".format(
            self.ent_apis_id
        )
        work.text = custom_escape(self.ent_dict.get("name"))
        for x in self.relation_notes():
            work.append(x)

        return work

    def create_event_node(self):
        event = ET.Element("{http://www.tei-c.org/ns/1.0}event")
        event.attrib["{http://www.w3.org/XML/1998/namespace}id"] = "event__{}".format(
            self.ent_apis_id
        )
        if self.ent_dict.get("start_date"):
            event.attrib["notBefore"] = self.ent_dict.get("start_date")
        if self.ent_dict.get("end_date"):
            event.attrib["notAfter"] = self.ent_dict.get("end_date")
        for x in self.relation_notes():
            event.append(x)
        label = ET.Element("label")
        label.text = self.ent_name
        event.append(label)
        if self.ent_dict.get("uris"):
            for x in self.ent_dict.get("uris"):
                event.attrib["ref"] = x.get("uri")
        return event

    def create_org_node(self):
        org = ET.Element("{http://www.tei-c.org/ns/1.0}org")
        org.attrib["{http://www.w3.org/XML/1998/namespace}id"] = "org__{}".format(
            self.ent_apis_id
        )
        orgName = ET.Element("orgName")
        orgName.text = self.ent_dict.get("name")
        if self.ent_dict.get("labels"):
            for x in self.ent_dict.get("labels"):
                node = ET.Element("orgName")
                node.attrib["type"] = "alt"
                try:
                    node_subtype = f'{x["label_type"]["name"]}'
                except KeyError:
                    node_subtype = False
                if node_subtype:
                    node.attrib["subtype"] = slugify(node_subtype)
                try:
                    node.attrib[
                        "{http://www.w3.org/XML/1998/namespace}lang"
                    ] = "{}".format(x["isoCode_639_3"])
                except KeyError:
                    pass
                node.text = x["label"]
                org.append(node)
        if self.ent_dict.get("start_date"):
            orgName.attrib["notBefore"] = self.ent_dict.get("start_date")
        if self.ent_dict.get("end_date"):
            orgName.attrib["notAfter"] = self.ent_dict.get("end_date")
        org.append(orgName)
        if self.uris_to_idnos():
            for x in self.uris_to_idnos():
                org.append(x)
        for x in self.relation_notes():
            org.append(x)
        return org

    def create_place_node(self):
        place = ET.Element("{http://www.tei-c.org/ns/1.0}place")
        place.attrib["{http://www.w3.org/XML/1998/namespace}id"] = "place__{}".format(
            self.ent_apis_id
        )
        placeName = ET.Element("placeName")
        placeName.text = self.ent_dict.get("name")
        if self.ent_dict.get("start_date"):
            placeName.attrib["notBefore"] = self.ent_dict.get("start_date")
        if self.ent_dict.get("end_date"):
            placeName.attrib["notAfter"] = self.ent_dict.get("end_date")
        place.append(placeName)
        if self.ent_dict.get("labels"):
            for x in self.ent_dict.get("labels"):
                node = ET.Element("placeName")
                node.attrib["type"] = "alt"
                try:
                    node_subtype = f'{x["label_type"]["name"]}'
                except KeyError:
                    node_subtype = False
                if node_subtype:
                    node.attrib["subtype"] = slugify(node_subtype)
                try:
                    node.attrib[
                        "{http://www.w3.org/XML/1998/namespace}lang"
                    ] = "{}".format(x["isoCode_639_3"])
                except KeyError:
                    pass
                node.text = x["label"]
                place.append(node)
        if self.ent_dict.get("lat"):
            coords = "{} {}".format(self.ent_dict["lat"], self.ent_dict["lng"])
            location = ET.Element("location")
            geo = ET.Element("geo")
            geo.text = coords
            location.append(geo)
            place.append(location)
        for x in self.relation_notes():
            place.append(x)
        if self.uris_to_idnos():
            for x in self.uris_to_idnos():
                place.append(x)
        return place

    def create_person_node(self):
        person = ET.Element("{http://www.tei-c.org/ns/1.0}person")
        person.attrib["{http://www.w3.org/XML/1998/namespace}id"] = "person__{}".format(
            self.ent_apis_id
        )
        persName = ET.Element("persName")
        surname = ET.Element("surname")
        surname.text = self.ent_dict.get("name")
        persName.append(surname)
        if self.ent_dict.get("first_name"):
            forename = ET.Element("forename")
            forename.text = self.ent_dict.get("first_name")
            persName.append(forename)
        person.append(persName)
        if self.ent_dict.get("labels"):
            for x in self.ent_dict.get("labels"):
                node = ET.Element("persName")
                node.attrib["type"] = "alt"
                try:
                    node_subtype = f'{x["label_type"]["name"]}'
                except KeyError:
                    node_subtype = False
                if node_subtype:
                    node.attrib["subtype"] = slugify(node_subtype)
                try:
                    node.attrib[
                        "{http://www.w3.org/XML/1998/namespace}lang"
                    ] = "{}".format(x["isoCode_639_3"])
                except KeyError:
                    pass
                node.text = x["label"]
                person.append(node)
        if self.ent_dict.get("start_date"):
            birth = ET.Element("birth")
            birth.attrib["when"] = self.ent_dict.get("start_date")
            birth.text = self.ent_dict.get("start_date_written")
            # If we wanted to add birth place, we'd need a specific lookup on
            # the place rel types here ... relations["places"]["relation_type"]["label"] == "BirthPlace"

            # It seems the only way to do this is to specify something in a controlled vocabulary --- some form of special status;

            if self.ent_dict.get("relations") and self.ent_dict.get("relations").get(
                "places"
            ):
                places = self.ent_dict.get("relations").get("places")
                pass

            person.append(birth)
        if self.ent_dict.get("end_date"):
            death = ET.Element("death")
            death.attrib["when"] = self.ent_dict.get("end_date")
            death.text = self.ent_dict.get("end_date_written")
            person.append(death)
        if self.ent_dict.get("profession"):
            for x in self.ent_dict.get("profession"):
                node = ET.Element("occupation")
                node.attrib["scheme"] = "#apis_vocabularies/professiontype/"
                node.attrib["code"] = "#{}".format(x["id"])
                node.text = x["name"]
                person.append(node)
        for x in self.relation_notes():
            person.append(x)
        if self.uris_to_idnos():
            for x in self.uris_to_idnos():
                person.append(x)
        return person

    def populate_header(self):
        main = f"{self.ent_type}: {self.ent_name}"
        header = self.gen_tei_header.format(main, self.project)
        return header

    def create_header_node(self):
        header = ET.fromstring(self.populate_header())
        return header

    def create_full_doc(self):
        ent_list = []
        doc = self.create_header_node()
        item = None
        if self.ent_type == "Person":
            item = self.create_person_node()
            ent_list = ET.Element("listPerson")
        elif self.ent_type == "Place":
            item = self.create_place_node()
            ent_list = ET.Element("listPlace")
        elif self.ent_type == "Institution":
            item = self.create_org_node()
            ent_list = ET.Element("listOrg")
        elif self.ent_type == "Event":
            item = self.create_event_node()
            ent_list = ET.Element("listEvent")
        elif self.ent_type == "Work":
            item = self.create_work_node()
            ent_list = ET.Element("list")
        # xpath modified to add entity nodes to <text type="entity"/>
        body = doc.xpath('//tei:text[@type="entity"]/tei:body', namespaces=self.nsmap)[
            0
        ]
        try:
            body.append(ent_list)
        except TypeError:
            pass
        ent_list.append(item)

        # Insert annotated texts into doc, as a separate text under
        # //tei:group
        groups = doc.xpath("//tei:group", namespaces=self.nsmap)[0]
        for text in self.build_annotated_texts_objects():
            groups.append(text)

        return doc

    def build_annotated_texts_objects(self):
        # Get annotations grouped by text

        annotations_by_text_id = group_annotations_by_text(self.ent_dict)

        texts = []

        # Here, we need to look up the entity in the DB
        ####  IDEALLY, pre-do this in initial query and add to ent_dict
        # though, this is likely to be quite a lot of stuff when not necessary...
        this_entity = entity_type_string_to_class[self.ent_type].objects.get(
            pk=self.ent_apis_id
        )
        this_entity_texts = {t for t in this_entity.text.all() if t.text}

        print([text.id for text in this_entity_texts])

        # Then, check all the entity texts to see whether it's an annotated one;
        # otherwise, we'll need to include it here...
        for text in this_entity_texts:
            if str(text.id) not in annotations_by_text_id:
                wrapped_text = "<p>{}</p>".format(
                    "</p><p>".join(text.text.split("\n\n"))
                )
                # Embed the text in some TEI tags
                embedded_text = '<text xml:id="text__{}"><body>{}</body></text>'.format(
                    text.id, wrapped_text
                )
                texts.append(embedded_text)

        # This loop here iterates texts from self.ent_dict annotations and embeds
        # annotations as TEI tags
        for text_id, anns in annotations_by_text_id.items():

            # Get the text object from database via its ID
            ### (in future, this should be embedded in ent_dict to avoid further query??)
            text_obj = Text.objects.get(pk=text_id)
            text_obj_pk = text_obj.tempentityclass_set.first().pk

            # If we *don't* want to include other entity_tagged texts,
            # skip this text if the object to which the text is not the
            # object we're serializing
            if not self.include_entity_tagged_texts and text_obj_pk != self.ent_apis_id:
                continue

            # On the other hand, if there is a text attached to this entity,
            # we might want to serialize it even if there is no annotation mentioning
            # this entity... (TAKEN CARE OF ABOVE)

            # Convert each annotation range from string-offset field ('34-52') into start and end indexes, and convert into tuple
            # of (start, end, tag) to run through standoff_to_inline function
            # (tag arg is got through looking up annotation type in relation_type_to_tei_tag — customisable
            # lookup at the top of this file)
            annotations = [
                (
                    int(ann["string_offset"].split("-")[0]),
                    int(ann["string_offset"].split("-")[1]),
                    f'{relation_type_to_tei_tag[ann["annotation_type"]]} ref="{ann["target"]}"',
                )
                for ann in anns
            ]

            tagged_text = stand_off_to_inline(text_obj.text, annotations)

            # Assuming the text has two-line separated paragraphs, wrap them in <p> tags
            wrapped_text = "<p>{}</p>".format("</p><p>".join(tagged_text.split("\n\n")))

            # Embed the text in some TEI tags
            embedded_text = '<text xml:id="text__{}"><body>{}</body></text>'.format(
                text_obj.id, wrapped_text
            )
            texts.append(embedded_text)

        # For each text string, convert to ET element
        texts = [convert_to_etree(text_as_string) for text_as_string in texts]
        return texts

    def serialize_full_doc(self):
        return ET.tostring(self.create_full_doc(), pretty_print=True, encoding="UTF-8")

    def export_full_doc(self):
        file = "temp.xml"
        with open(file, "wb") as f:
            f.write(
                ET.tostring(self.create_full_doc(), pretty_print=True, encoding="UTF-8")
            )
        return file


def convert_to_etree(text_as_string):
    # Function here to catch any XML syntax errors
    try:
        return ET.fromstring(text_as_string)
    # If there's some problem, most likely overlapping hierarchies,
    # we should return something to serialize
    except ET.XMLSyntaxError:
        return ET.fromstring(
            '<text type="conversion-error"><!-- There was an error inserting annotations into this document, probably due to overlaps --></text>'
        )


def group_annotations_by_text(ent_dict):
    annotations_by_text = defaultdict(list)

    for rel_type_name, rel_type_list in ent_dict.get("relations").items():

        for rel in rel_type_list:

            if rel.get("annotation"):
                for ann in rel.get("annotation", []):
                    text_id = ann["text_url"].split("/")[
                        -2
                    ]  # parse the url to get the text id...
                    target = rel.get("target", {}).get("url", None)
                    # add the annotation to the text-group, also adding in a type for conversion later
                    annotations_by_text[text_id].append(
                        {**ann, "annotation_type": rel_type_name, "target": target}
                    )

    return annotations_by_text


def stand_off_to_inline(text, annot):
    """
    Function from: https://gist.github.com/emsrc/c7aba4506214a20505ed

    Convert stand-off annotation to inline annotation
    Parameters
    ----------
    text : str
        unannotated text
    annot: list of tuples
        stand-off annotation as tuples in the form (i, j, tag)
        where integers i and j are the start and end character offset,
        and tag is a string for the tag label and - optionally - attributes.
    Returns
    -------
    inline: str
        text in xml format with inline annotation
    Notes
    -----
    Will not detect partly overlapping text spans, which will give rise
    to ill-formed xml.
    """
    # sort on decreasing span size
    annot.sort(key=lambda t: t[1] - t[0], reverse=True)

    # create dict mapping offsets to tags
    offsets2tags = defaultdict(list)

    for start, end, tag in annot:
        offsets2tags[start].append("<{}>".format(tag))
        offsets2tags[end].insert(0, "</{}>".format(tag.split()[0]))

    # merge text and tags
    parts = []
    i = None

    for j in sorted(offsets2tags.keys()) + [None]:
        parts.append(text[i:j])
        tags = "".join(offsets2tags[j])
        parts.append(tags)
        i = j

    return "".join(parts)

