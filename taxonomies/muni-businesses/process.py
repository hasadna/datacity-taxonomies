from dataflows import Flow, add_computed_field, delete_fields, \
    printer, set_type

from dgp.core.base_enricher import ColumnTypeTester, ColumnReplacer, \
        DatapackageJoiner, enrichments_flows, BaseEnricher, DuplicateRemover
from dgp.config.consts import RESOURCE_NAME

from datacity_server.processors import MunicipalityNameToCodeEnricher, \
    FilterEmptyFields, AddressFixer, GeoCoder


class FilterEmptyCodes(FilterEmptyFields):
    FIELDS_TO_CHECK = {
        'business-kind': None,
        'address-full': None,
        'business-name': None,
        'property-code': None
    }


class SelectOneUniqueItem(DuplicateRemover):
    ORDER_BY_KEY = '{business-name}{property-code}'


def flows(config, context):
    return enrichments_flows(
        config, context,
        MunicipalityNameToCodeEnricher,
        FilterEmptyCodes,
        SelectOneUniqueItem,
        AddressFixer,
        GeoCoder,
    )
