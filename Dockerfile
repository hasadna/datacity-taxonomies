FROM akariv/dgp-server:latest

ADD taxonomies /dgp/taxonomies/
ADD datacity_server /dgp/datacity_server/

RUN echo "http://nl.alpinelinux.org/alpine/edge/main" > /etc/apk/repositories && \
    echo "http://nl.alpinelinux.org/alpine/edge/community" >> /etc/apk/repositories && \
    echo "http://nl.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories && cat /etc/apk/repositories && \
    apk --update --no-cache --virtual=build-dependencies add \
        build-base python3-dev libxml2-dev libxslt-dev && \
    apk add --update --no-cache --upgrade libstdc++ proj-util proj-dev  && proj && \
    pip install --no-cache-dir pyproj && \
    apk del build-dependencies && rm -rf /var/cache/apk/*

ADD requirements.txt /dgp
RUN python -m pip install -r /dgp/requirements.txt

ADD requirements-dev.txt /dgp
RUN python -m pip install -U -r /dgp/requirements-dev.txt

ENV SERVER_MODULE=datacity_server.server:app

WORKDIR /dgp/
