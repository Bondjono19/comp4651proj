import psycopg
from flask import g, current_app
def init_database(app):
    app.teardon_appcontext(close_connection)

def get_database():
    if 'db' not in g:
        g.db = psycopg.connect(current_app.config['DATABASE_URL'])
    return g.db
def close_connection(e=None):
    db = g.pop('db',None)
    if db is not None:
        db.close()

