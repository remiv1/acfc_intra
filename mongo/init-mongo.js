db = db.getSiblingDB('logDB');

db.users.insertMany([
  { name: "log_user_db" }
]);