FROM sameersbn/squid:3.5.27-2

ENV USE_ACL=0

RUN    apt-get update \
    && apt-get install -y git golang \
    && apt-get clean \
    && rm -rf /var/cache/apt/archives/* /var/lib/apt/lists/*

RUN go get github.com/rchunping/squid-urlrewrite
RUN mv /root/go/bin/squid-urlrewrite /usr/local/bin

RUN apt-get remove -y git golang

COPY squid.conf /etc/squid/squid.conf
COPY squid-urlrewrite.conf /etc/squid-urlrewrite.conf
