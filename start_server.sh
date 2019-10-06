#!/bin/bash
gunicorn -w 4 -t 180 --bind 0.0.0.0:9000 datacity_server.server:app --worker-class aiohttp.GunicornWebWorker
