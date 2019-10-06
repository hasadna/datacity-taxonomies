FROM akariv/dgp-server:latest

ADD taxonomies /dgp/taxonomies/
ADD datacity_server /dgp/datacity_server/

ADD requirements.txt /dgp
RUN python -m pip install -r /dgp/requirements.txt

ADD requirements-dev.txt /dgp
RUN python -m pip install -U -r /dgp/requirements-dev.txt

ENV SERVER_MODULE=datacity_server.server:app

WORKDIR /dgp/
