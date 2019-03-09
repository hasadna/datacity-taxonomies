from dataflows import Flow, add_computed_field

from dgp.core.base_enricher import ColumnTypeTester, \
        DatapackageJoiner, enrichments_flows


class MunicipalityNameToCodeEnricher(ColumnTypeTester, DatapackageJoiner):

    REQUIRED_COLUMN_TYPES = ['municipality:name']
    PROHIBITED_COLUMN_TYPES = ['municipality:code']
    REF_DATAPACKAGE = 'http://next.obudget.org/datapackages/lamas-municipal-data/datapackage.json'
    REF_KEY_FIELDS = ['name_municipality']
    REF_FETCH_FIELDS = ['symbol_municipality_2015']
    SOURCE_KEY_FIELDS = ['municipality-name']
    TARGET_FIELD_COLUMNTYPES = ['municipality:code']


class CardFunctionalCodeSplitter(ColumnTypeTester):

    REQUIRED_COLUMN_TYPES = ['card:code']
    PROHIBITED_COLUMN_TYPES = [f'functional-classification:moin:level{i}:code' for i in range(1, 5)]

    def postflow(self):

        new_fields = [x.replace(':', '-') for x in self.PROHIBITED_COLUMN_TYPES]

        def split_code(rows):
            if rows.res.name != 'out':
                yield from rows
            else:
                for row in rows:
                    for i, f in enumerate(new_fields):
                        row[f] = row['card-code'][1:i+2]
                    yield row

        return Flow(
            add_computed_field([dict(
                target=f,
                operation='constant',
            ) for f in new_fields]),
            split_code
        )


class CardEconomicCodeSplitter(ColumnTypeTester):

    REQUIRED_COLUMN_TYPES = ['card:code']
    PROHIBITED_COLUMN_TYPES = [f'economic-classification:moin:level{i}:code' for i in range(1, 4)]

    def postflow(self):

        new_fields = [x.replace(':', '-') for x in self.PROHIBITED_COLUMN_TYPES]

        def split_code(rows):
            if rows.res.name != 'out':
                yield from rows
            else:
                for row in rows:
                    for i, f in enumerate(new_fields):
                        row[f] = row['card-code'][-3:][:i+1]
                    yield row

        return Flow(
            add_computed_field([dict(
                target=f,
                operation='constant',
            ) for f in new_fields]),
            split_code
        )


class CardCodeToOfficialCardName(ColumnTypeTester, DatapackageJoiner):

    REQUIRED_COLUMN_TYPES = []

    REF_KEY_FIELDS = ['CODE']
    REF_FETCH_FIELDS = ['NAME']


class CardFCodeToOfficialCardName(CardCodeToOfficialCardName):

    REF_DATAPACKAGE = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTsUyG1zNWeE2rlosEVNK48p9j9MALG-IIymIPcOF9Rz3T0rt6G6iFeqNXFoQYlMnNKZG5ZGTHcq4-z/pub?gid=180266534&single=true&output=csv'


class CardECodeToOfficialCardName(CardCodeToOfficialCardName):

    REF_DATAPACKAGE = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTsUyG1zNWeE2rlosEVNK48p9j9MALG-IIymIPcOF9Rz3T0rt6G6iFeqNXFoQYlMnNKZG5ZGTHcq4-z/pub?gid=1435201518&single=true&output=csv'
    REF_KEY_FIELDS = ['CODE', 'DIRECTION']


class CardCode1ToDirection(CardFCodeToOfficialCardName):

    REF_FETCH_FIELDS = ['DIRECTION']
    PROHIBITED_COLUMN_TYPES = ['direction:code']
    SOURCE_KEY_FIELDS = ['functional-classification-moin-level1-code']
    TARGET_FIELD_COLUMNTYPES = ['direction:code']


class CardCode1ToOfficialCardName(CardFCodeToOfficialCardName):

    PROHIBITED_COLUMN_TYPES = ['functional-classification:moin:level1:name']
    SOURCE_KEY_FIELDS = ['functional-classification-moin-level1-code']
    TARGET_FIELD_COLUMNTYPES = ['functional-classification:moin:level1:name']


class CardCode2ToOfficialCardName(CardFCodeToOfficialCardName):

    PROHIBITED_COLUMN_TYPES = ['functional-classification:moin:level2:name']
    SOURCE_KEY_FIELDS = ['functional-classification-moin-level2-code']
    TARGET_FIELD_COLUMNTYPES = ['functional-classification:moin:level2:name']


class CardCode3ToOfficialCardName(CardFCodeToOfficialCardName):

    PROHIBITED_COLUMN_TYPES = ['functional-classification:moin:level3:name']
    SOURCE_KEY_FIELDS = ['functional-classification-moin-level3-code']
    TARGET_FIELD_COLUMNTYPES = ['functional-classification:moin:level3:name']


class CardCode4ToOfficialCardName(CardFCodeToOfficialCardName):

    PROHIBITED_COLUMN_TYPES = ['functional-classification:moin:level4:name']
    SOURCE_KEY_FIELDS = ['functional-classification-moin-level4-code']
    TARGET_FIELD_COLUMNTYPES = ['functional-classification:moin:level4:name']


class CardECode1ToOfficialCardName(CardECodeToOfficialCardName):

    PROHIBITED_COLUMN_TYPES = ['economic-classification:moin:level1:name']
    SOURCE_KEY_FIELDS = ['economic-classification-moin-level1-code', 'direction-code']
    TARGET_FIELD_COLUMNTYPES = ['economic-classification:moin:level1:name']


class CardECode2ToOfficialCardName(CardECodeToOfficialCardName):

    PROHIBITED_COLUMN_TYPES = ['economic-classification:moin:level2:name']
    SOURCE_KEY_FIELDS = ['economic-classification-moin-level2-code', 'direction-code']
    TARGET_FIELD_COLUMNTYPES = ['economic-classification:moin:level2:name']


class CardECode3ToOfficialCardName(CardECodeToOfficialCardName):

    PROHIBITED_COLUMN_TYPES = ['economic-classification:moin:level3:name']
    SOURCE_KEY_FIELDS = ['economic-classification-moin-level3-code', 'direction-code']
    TARGET_FIELD_COLUMNTYPES = ['economic-classification:moin:level3:name']


def flows(config, context):
    return enrichments_flows(
        config, context,
        MunicipalityNameToCodeEnricher,
        CardFunctionalCodeSplitter,
        CardEconomicCodeSplitter,
        CardCode1ToDirection,
        CardCode1ToOfficialCardName,
        CardCode2ToOfficialCardName,
        CardCode3ToOfficialCardName,
        CardCode4ToOfficialCardName,
        CardECode1ToOfficialCardName,
        CardECode2ToOfficialCardName,
        CardECode3ToOfficialCardName,
    )
