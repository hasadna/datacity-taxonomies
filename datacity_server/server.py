import os
import logging

from aiohttp import web
import aiopg.sa

from .datacity_dgp_server import DatacityDgpServer
from .configurations import configs

app = web.Application()
app.add_subapp('/api', DatacityDgpServer())
app.router.add_get('/configs', configs)


async def init_pg(app):
    engine = await aiopg.sa.create_engine(os.environ['DATABASE_URL'])
    app['db'] = engine


async def close_pg(app):
    app['db'].close()
    await app['db'].wait_closed()


app.on_startup.append(init_pg)
app.on_cleanup.append(close_pg)

logging.getLogger().setLevel(logging.INFO)

if __name__ == "__main__":
    web.run_app(app, host='127.0.0.1', port=8000, access_log=logging.getLogger())
