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
                idno.text = x.get('uri')
                uris.append(idno)
        return uris

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
        item = self.create_person_node()
        body = doc.xpath("//tei:body", namespaces=self.nsmap)[0]
        body.append(item)
        return doc

    def serialize_full_doc(self):
        return ET.tostring(self.create_full_doc(), pretty_print=True, encoding='UTF-8')

    def export_full_doc(self):
        file = "temp.xml"
        with open(file, 'wb') as f:
            f.write(ET.tostring(self.create_full_doc(), pretty_print=True, encoding='UTF-8'))
        return file
