import os

from main import app
from config import TestConfig
from shared.instances import mdb, init_firebase

app.config.from_object(TestConfig)
mdb.init_app(app)
init_firebase(TestConfig)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
