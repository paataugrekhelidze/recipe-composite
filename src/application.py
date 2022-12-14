from flask import Flask, Response, request
from flask_cors import CORS
from compositer import compositer

# Create the Flask application object.
app = Flask(__name__)
CORS(app)

app.register_blueprint(compositer)
@app.before_request
def before_request():
    logged_in = requests.get(os.environ["API_ENDPOINT"] + "/auth/is_logged_in").status_code==200
    if not logged_in:
        return Response("NOT AUTHENTICATED", status=401, content_type="text/plain")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5015, debug=True)
