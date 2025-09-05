db = db.getSiblingDB("${MONGO_INITDB_DATABASE}");

db.createUser({
  user: "${MONGO_APP_USER}",
  pwd: "${MONGO_APP_PASSWORD}",
  roles: [ { role: "readWrite", db: "${MONGO_INITDB_DATABASE}" } ]
});