from flask import Flask, Response, request
from flask_cors import CORS
from compositer import compositer

# Create the Flask application object.
app = Flask(__name__)
CORS(app)

app.register_blueprint(compositer)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5015, debug=True)
