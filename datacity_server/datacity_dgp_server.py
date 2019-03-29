import os

from dgp_server.blueprint import DgpServer

from dataflows import Flow, join_self, add_computed_field, printer, duplicate, \
    set_type, set_primary_key, dump_to_sql
from dgp.core import Context, Config
from dgp.taxonomies import Taxonomy
from dgp.genera.consts import RESOURCE_NAME


class DatacityDgpServer(DgpServer):

    def __init__(self):
        super().__init__(
            os.environ.get('BASE_PATH', '/var/dgp'),
            os.environ.get('DATABASE_URL')
        )

    def publish_flow(self, config: Config, context: Context):
        super_flow = super().publish_flow(config, context)
        if super_flow is not None:
            return Flow(
                super_flow,
                self.store_config(config, context.taxonomy)
            )

    def collate_values(self, fields, field):
        def func(package):
            def process(rows):
                for row in rows:
                    row[field] = dict((f, row[f]) for f in fields)
                    yield row

            yield package.pkg
            for i, res in enumerate(package):
                if i == 0:
                    yield res
                else:
                    yield process(res)

        return func

    def store_config(self, config: Config, taxonomy: Taxonomy):
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
        saved_config = config._unflatten()
        saved_config.setdefault('publish', {})['allowed'] = False

        return Flow(
            duplicate(RESOURCE_NAME, TARGET),
            join_self(
                TARGET,
                all_fields,
                TARGET,
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
                    dict(
                        operation='constant',
                        target='config',
                        with_=saved_config
                    )
                ],
                resources=TARGET
            ),
            self.collate_values(fields, 'key_values'),
            join_self(
                TARGET,
                ['_source'],
                TARGET,
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
                engine=self.engine,
            ),
        )
