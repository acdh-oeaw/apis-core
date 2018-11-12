import lxml.etree as ET

from . partials import TEI_NSMAP, tei_gen_header


class TeiEntCreator():
    def __init__(self, ent_dict):
        self.nsmap = TEI_NSMAP
        self.project = "APIS"
        self.ent_dict = ent_dict
        self.ent_name = ent_dict.get('name', 'No name provided')
        self.ent_type = ent_dict.get('entity_type')
        self.ent_apis_id = ent_dict.get('id')
        self.gen_tei_header = tei_gen_header

    def uris_to_idnos(self):
        uris = []
        if self.ent_dict.get('uris'):
            for x in self.ent_dict.get('uris'):
                idno = ET.Element("idno")
                idno.attrib['type'] = 'URL'
                if "d-nb.info" in x.get('uri'):
                    idno.attrib['subtype'] = "GND"
                idno.text = x.get('uri')
                uris.append(idno)
        return uris

    def create_event_node(self):
        event = ET.Element("{http://www.tei-c.org/ns/1.0}event")
        event.attrib['{http://www.w3.org/XML/1998/namespace}id'] = "event__{}".format(
            self.ent_apis_id
        )
        if self.ent_dict.get('start_date'):
            event.attrib['notBefore'] = self.ent_dict.get('start_date')
        if self.ent_dict.get('end_date'):
            event.attrib['notAfter'] = self.ent_dict.get('end_date')
        label = ET.Element("label")
        label.text = self.ent_dict.get('name')
        event.append(label)
        if self.ent_dict.get('uris'):
            for x in self.ent_dict.get('uris'):
                event.attrib['ref'] = x.get('uri')
        return event

    def create_org_node(self):
        org = ET.Element("{http://www.tei-c.org/ns/1.0}org")
        org.attrib['{http://www.w3.org/XML/1998/namespace}id'] = "org__{}".format(
            self.ent_apis_id
        )
        orgName = ET.Element("orgName")
        orgName.text = self.ent_dict.get('name')
        if self.ent_dict.get('start_date'):
            orgName.attrib['notBefore'] = self.ent_dict.get('start_date')
        if self.ent_dict.get('end_date'):
            orgName.attrib['notAfter'] = self.ent_dict.get('end_date')
        org.append(orgName)
        if self.uris_to_idnos():
            for x in self.uris_to_idnos():
                org.append(x)
        return org

    def create_place_node(self):
        place = ET.Element("{http://www.tei-c.org/ns/1.0}place")
        place.attrib['{http://www.w3.org/XML/1998/namespace}id'] = "place__{}".format(
            self.ent_apis_id
        )
        placeName = ET.Element("placeName")
        placeName.text = self.ent_dict.get('name')
        if self.ent_dict.get('start_date'):
            placeName.attrib['notBefore'] = self.ent_dict.get('start_date')
        if self.ent_dict.get('end_date'):
            placeName.attrib['notAfter'] = self.ent_dict.get('end_date')
        place.append(placeName)
        if self.uris_to_idnos():
            for x in self.uris_to_idnos():
                place.append(x)
        if self.ent_dict.get('lat'):
            coords = "{} {}".format(self.ent_dict['lat'], self.ent_dict['lng'])
            location = ET.Element('location')
            geo = ET.Element('geo')
            geo.text = coords
            location.append(geo)
            place.append(location)
        return place

    def create_person_node(self):
        person = ET.Element("{http://www.tei-c.org/ns/1.0}person")
        person.attrib['{http://www.w3.org/XML/1998/namespace}id'] = "person__{}".format(
            self.ent_apis_id
        )
        persName = ET.Element("persName")
        surname = ET.Element("surname")
        surname.text = self.ent_dict.get('name')
        persName.append(surname)
        if self.ent_dict.get('first_name'):
            forename = ET.Element("forename")
            forename.text = self.ent_dict.get('first_name')
            persName.append(forename)
        person.append(persName)
        if self.ent_dict.get('start_date'):
            birth = ET.Element("birth")
            birth.attrib['when'] = self.ent_dict.get('start_date')
            birth.text = self.ent_dict.get('start_date_written')
            person.append(birth)
        if self.ent_dict.get('end_date'):
            death = ET.Element("death")
            death.attrib['when'] = self.ent_dict.get('end_date')
            death.text = self.ent_dict.get('end_date_written')
            person.append(death)
        if self.uris_to_idnos():
            for x in self.uris_to_idnos():
                person.append(x)
        return person

    def populate_header(self):
        main = "{}: {}".format(self.ent_type, self.ent_name)
        header = self.gen_tei_header.format(main, self.project)
        return header

    def create_header_node(self):
        header = ET.fromstring(self.populate_header())
        return header

    def create_full_doc(self):
        doc = self.create_header_node()
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
        body = doc.xpath("//tei:body", namespaces=self.nsmap)[0]
        body.append(ent_list)
        ent_list.append(item)
        return doc

    def serialize_full_doc(self):
        return ET.tostring(self.create_full_doc(), pretty_print=True, encoding='UTF-8')

    def export_full_doc(self):
        file = "temp.xml"
        with open(file, 'wb') as f:
            f.write(ET.tostring(self.create_full_doc(), pretty_print=True, encoding='UTF-8'))
        return file
