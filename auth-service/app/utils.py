import jwt, datetime
from flask import current_app
def generate_jwt(userid):
    payload = {
        "sub": userid,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    }
    token = jwt.encode(payload,current_app.config['JWT_SECRET'])
    return token