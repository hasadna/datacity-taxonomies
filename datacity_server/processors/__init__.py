import geocoder
import requests

from dataflows import Flow, add_field
from dgp.core.base_enricher import BaseEnricher, \
    DatapackageJoiner, ColumnTypeTester
from dgp.config.consts import RESOURCE_NAME


class MunicipalityNameToCodeEnricher(DatapackageJoiner):

    REQUIRED_COLUMN_TYPES = ['municipality:name']
    PROHIBITED_COLUMN_TYPES = ['municipality:code']
    REF_DATAPACKAGE = 'http://next.obudget.org/datapackages/lamas-municipal-data/datapackage.json'
    REF_KEY_FIELDS = ['name_municipality']
    REF_FETCH_FIELDS = ['symbol_municipality_2015']
    SOURCE_KEY_FIELDS = ['municipality-name']
    TARGET_FIELD_COLUMNTYPES = ['municipality:code']


class FilterEmptyFields(BaseEnricher):

    FIELDS_TO_CHECK = {}

    def __init__(self, *args):
        super().__init__(*args)
        self.fields = self.FIELDS_TO_CHECK

    def test(self):
        return True

    def verify(self, row):
        for field, validator in self.fields.items():
            if field not in row:
                continue
            if not row[field]:
                return False
            if callable(validator):
                if not validator(row):
                    return False
        return True

    def work(self):
        def func(package):
            yield package.pkg
            for i, res in enumerate(package):
                if i != len(package.pkg.resources) - 1:
                    yield res
                else:
                    yield filter(self.verify, res)
        return func

    def postflow(self):
        return Flow(self.work())


class AddressFixer(BaseEnricher):

    def test(self):
        return True

    def combine_addresses(self, row):
        addresses = [
            str(row[field])
            for field in
            ('address-' + suffix
             for suffix in ('full', 'street', 'house-number', 'city'))
            if field in row and row.get(field)
        ]
        if len(addresses) > 0:
            row['address-full'] = ', '.join(addresses)
        return row

    def address_fixer(self):
        def func(package):
            address_fields = [
                f['name'].replace('address-', '')
                for f in package.pkg.descriptor['resources'][-1]['schema']['fields']
                if f['name'].startswith('address-')
            ]
            if len(address_fields) > 0 and 'full' not in address_fields:
                package.pkg.descriptor['resources'][-1]['schema']['fields'].append(dict(
                    name='address-full',
                    columnType='address:full',
                    type='string'
                ))
            yield package.pkg
            for i, res in enumerate(package):
                if i == len(package.pkg.resources) - 1:
                    yield (self.combine_addresses(r) for r in res)
                else:
                    yield res
        return func

    def postflow(self):
        return Flow(
            self.address_fixer(),
        )


class GeoCoder(ColumnTypeTester):

    REQUIRED_COLUMN_TYPES = ['address:full']
    PROHIBITED_COLUMN_TYPES = ['location:lat', 'location:lon']

    def geocode(self):
        session = requests.Session()
        cache = {}

        def func(row):
            address = row.get('address-full')
            if address and address.strip():
                address = address.strip()
                for prefix in ('שד', 'רח', 'רחוב'):
                    if address.startswith(prefix + ' '):
                        address = address[len(prefix)+1:]
                        break
                if address in cache:
                    result = cache[address]
                else:
                    g = geocoder.osm(address, session=session, url='https://geocode.datacity.org.il/')
                    if g.ok and g.lat and g.lng:
                        result = (g.lat, g.lng)
                    else:
                        result = None
                    cache[address] = result
                if result:
                    row['location-lat'], row['location-lon'] = result

        return func

    def conditional(self):
        return Flow(
            add_field('location-lat', 'number',
                      resources=RESOURCE_NAME, columnType='location:lat'),
            add_field('location-lon', 'number',
                      resources=RESOURCE_NAME, columnType='location:lon'),
            self.geocode()
        )
