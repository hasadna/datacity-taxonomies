FROM akariv/dgp-server:latest

ADD taxonomies /dgp/taxonomies/
ADD datacity_server /dgp/datacity_server/

ENV SERVER_MODULE=datacity_server.server:app

WORKDIR /dgp/
