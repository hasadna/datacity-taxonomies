import re

from dataflows import Flow, add_computed_field, delete_fields, \
    printer, set_type

from dgp.core.base_enricher import ColumnTypeTester, ColumnReplacer, \
        DatapackageJoiner, enrichments_flows, BaseEnricher, DuplicateRemover
from dgp.config.consts import RESOURCE_NAME

from datacity_server.processors import MunicipalityNameToCodeEnricher


class SelectLatestProcessEnricher(DuplicateRemover):

    ORDER_BY_KEY = '{process-publication-date}'


class FilterEmptyCodes(BaseEnricher):

    def test(self):
        return True

    def work(self):
        valid_codes = re.compile('[0-9/]+')

        def func(package):
            yield package.pkg
            for i, res in enumerate(package):
                if i != len(package.pkg.resources) - 1:
                    yield res
                else:
                    yield filter(
                        lambda row: (
                            'process-code' not in row or
                            (row['process-code'] and valid_codes.fullmatch(row['process-code']))
                        ),
                        res
                    )
        return func

    def postflow(self):
        return Flow(self.work())


def flows(config, context):
    return enrichments_flows(
        config, context,
        FilterEmptyCodes,
        MunicipalityNameToCodeEnricher,
        SelectLatestProcessEnricher,
    )
