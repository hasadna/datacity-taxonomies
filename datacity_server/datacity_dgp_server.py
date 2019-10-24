import os
import copy

from dgp_server.blueprint import DgpServer

from dataflows import Flow, add_computed_field, duplicate, \
    set_type, set_primary_key, dump_to_sql, add_field, join_with_self, \
    PackageWrapper, load
from dgp.core import Context, Config, BaseDataGenusProcessor
from dgp.config.consts import RESOURCE_NAME, CONFIG_TAXONOMY_CT, \
    CONFIG_TAXONOMY_ID


from .datacity_dgp import DataCityDGP


class ConfigStorerDGP(BaseDataGenusProcessor):

    def __init__(self, config, context, lazy_engine):
        super().__init__(config, context)
        self.lazy_engine = lazy_engine

    def collate_values(self, fields):
        def func(row):
            return dict((f, row[f]) for f in fields)
        return func

    def flow(self):
        taxonomy = self.context.taxonomy
        txn_config = taxonomy.config
        fmt_str = [taxonomy.title + ' עבור:']
        fields = txn_config['key-fields']
        for f in fields:
            for ct in taxonomy.column_types:
                if ct['name'] == f:
                    fmt_str.append(
                        '%s: "{%s}",' % (ct['title'], f.replace(':', '-'))
                    )
                    break
        fmt_str = ' '.join(fmt_str)
        fields = [
            ct.replace(':', '-')
            for ct in fields
        ]
        all_fields = ['_source'] + fields

        TARGET = 'configurations'
        saved_config = self.config._unflatten()
        saved_config.setdefault('publish', {})['allowed'] = False

        return Flow(
            duplicate(RESOURCE_NAME, TARGET),
            join_with_self(
                TARGET,
                all_fields,
                dict((f, {}) for f in all_fields),
            ),
            add_computed_field(
                [
                    dict(
                        operation='format',
                        target='snippets',
                        with_=fmt_str
                    ),
                    dict(
                        operation='constant',
                        target='key_values',
                        with_=None
                    ),
                ],
                resources=TARGET
            ),
            add_field('config', 'object', saved_config, resources=TARGET),
            add_field('fields', type='object',
                      default=self.collate_values(fields), resources=TARGET),
            join_with_self(
                TARGET,
                ['_source'],
                dict(
                    source=dict(name='_source'),
                    config={},
                    key_values=dict(aggregate='array'),
                    snippets=dict(aggregate='array'),
                )
            ),
            set_type('source', type='string'),
            set_type('config', type='object'),
            set_type('key_values', type='array'),
            set_type('snippets', type='array'),
            set_primary_key(['source']),
            dump_to_sql(
                dict([
                    (TARGET, {
                        'resource-name': TARGET,
                        'mode': 'update'
                    })
                ]),
                engine=self.lazy_engine(),
            ),
        )


class DBPreparerDGP(BaseDataGenusProcessor):

    def __init__(self, config, context, lazy_engine):
        super().__init__(config, context)
        self.lazy_engine = lazy_engine

    def fill_in_pks(self, res, pks):
        for row in res:
            for pk in pks:
                assert pk not in row, 'Found %s in %s' % (pk, row)
                row[pk] = ''
            yield row

    def add_missing_fields(self):

        def func(package: PackageWrapper):
            cts = {}
            pks = []
            for ct in self.config.get(CONFIG_TAXONOMY_CT):
                cts[ct['name'].replace(':', '-')] = ct

            descriptor = package.pkg.descriptor
            resource_idx = None
            for idx, res in enumerate(descriptor['resources']):
                if res['name'] == RESOURCE_NAME:
                    resource_idx = idx
                    fields = res['schema']['fields']
                    for field in fields:
                        if field['name'] in cts:
                            cts.pop(field['name'])
                    print('MISSING:', list(cts.keys()))
                    cts = list(cts.values())
                    for ct in cts:
                        ct_name = ct['name'].replace(':', '-')
                        fields.append(dict(
                            name=ct_name,
                            type=ct['dataType'],
                            **ct.get('options', {})
                        ))
                        if ct.get('unique'):
                            res['schema']['primaryKey'].append(ct_name)
                            pks.append(ct_name)
            if resource_idx is not None:
                descriptor = copy.deepcopy(descriptor)
                resource = descriptor['resources'][resource_idx]
                descriptor['resources'] = [resource]
                resource['schema']['fields'].append(dict(name='_source', type='string'))
                resource['schema']['primaryKey'].append('_source')
                table_name = self.config.get(CONFIG_TAXONOMY_ID)\
                    .replace('-', '_')
                Flow(
                    load((descriptor, [[]])),
                    dump_to_sql(
                        dict([
                            (table_name, {
                                'resource-name': RESOURCE_NAME,
                                'mode': 'update'
                            })
                        ]),
                        engine=self.lazy_engine(),
                    )
                ).process()
            yield package.pkg
            for res in package:
                if res.res.name == RESOURCE_NAME:
                    yield self.fill_in_pks(res, pks)
                else:
                    yield res
        return func

    def flow(self):
        return Flow(
            self.add_missing_fields()
        )


class DatacityDgpServer(DgpServer):

    def __init__(self):
        super().__init__(
            os.environ.get('BASE_PATH', '/var/dgp'),
            os.environ.get('DATABASE_URL'),
        )

    def loader_dgps(self, config: Config, context: Context):
        return [
            DataCityDGP
        ]

    def publish_flow(self, config: Config, context: Context):
        super_dgps = super().publish_flow(config, context)
        super_dgps.insert(
            0,
            DBPreparerDGP(config, context, self.lazy_engine())
        )
        super_dgps.append(
            ConfigStorerDGP(config, context, self.lazy_engine())
        )
        return super_dgps
