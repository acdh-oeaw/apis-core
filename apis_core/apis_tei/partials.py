TEI_NSMAP = {
    'tei': "http://www.tei-c.org/ns/1.0",
    'xml': "http://www.w3.org/XML/1998/namespace",
}


PERS_TO_TEI_DICT = {
    'name': "{http://www.tei-c.org/ns/1.0}surname",
    'first_name': "{http://www.tei-c.org/ns/1.0}forename",
    'start_date': "{http://www.tei-c.org/ns/1.0}birth",
    'end_date': "{http://www.tei-c.org/ns/1.0}death",
}


tei_gen_header = """
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <teiHeader>
        <fileDesc>
         <titleStmt>
            <title type="main">{}</title>
            <title type="sub">{}</title>
         </titleStmt>
         <publicationStmt>
            <p/>
         </publicationStmt>
         <sourceDesc>
            <p></p>
         </sourceDesc>
        </fileDesc>
    </teiHeader>
    <text>
        <group>
            <text type="entity">
                <body/>
            </text>
        </group>
      
    </text>
</TEI>
"""
