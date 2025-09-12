#!/bin/bash
envsubst < /docker-entrypoint-initdb.d/init-mongo.template.js > /docker-entrypoint-initdb.d/init-mongo.js
exec docker-entrypoint.sh mongod
