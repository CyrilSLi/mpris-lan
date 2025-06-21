# Built-in modules:
import io, json, logging, subprocess
from datetime import datetime
from html import unescape

# Third-party modules:
from flask import Flask, redirect, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.serving import make_server
import filetype, jsonschema

app = Flask (__name__)
CORS (app)
thumbnails = {}

with open ("control_schema.json") as f:
    control_schema = json.load (f)
mpris_keys = ["playerInstance", "position", "mpris:length", "status", "volume", "shuffle", "loop", "title", "artist", "mpris:artUrl"]

def run_playerctl (cmd):
    run = subprocess.run (cmd, capture_output = True)
    try:
        run.check_returncode ()
    except subprocess.CalledProcessError:
        if "No player could handle this command" in run.stderr.decode ("utf-8"):
            return (jsonify ({}), 200)
        return (jsonify ({"error": "playerctl command failed"}), 500)
    return run

@app.route ("/mpris", methods = ["GET", "POST"])
def mpris ():
    global control_schema, mpris_keys, thumbnails

    if request.method == "POST" and request.json:
        req = request.json
        schema = control_schema.copy ()
        schema ["properties"] ["players"] ["items"] ["enum"] = list (thumbnails.keys ()) # Only allow current players
        try:
            jsonschema.validate (req, schema)
        except jsonschema.ValidationError as e:
            return jsonify ({"error": str (e)}), 400
        return_args = run_playerctl (["playerctl", "-p", ",".join (req ["players"]), req ["command"], str (req.get ("value", ""))])
        if isinstance (return_args, tuple):
            return return_args

    return_args = run_playerctl (["playerctl", "-a", "metadata", "-f", "{{markup_escape(" + ")}}'{{markup_escape(".join (mpris_keys) + ")}}'"])
    if isinstance (return_args, tuple):
        return return_args

    thumbnails, resp = {}, {"__timestamp__": datetime.now ().timestamp ()}
    default = lambda x: None if x == "" else unescape (x)
    for player in return_args.stdout.decode ("utf-8").strip ().split ("\n"):
        values = player.split ("'")
        resp [default (values [0])] = {
            "position": int (values [1]) / 1000000, # Microseconds to seconds
            "length": int (values [2]) / 1000000,
            "status": default (values [3]),
            "volume": float (values [4]),
            "shuffle": default (values [5]),
            "loop": default (values [6]),
            "title": default (values [7]),
            "artist": default (values [8])
        }
        thumbnails [default (values [0])] = default (values [9]) or None

    return jsonify (resp)

@app.route ("/thumbnail", methods = ["GET"])
def thumbnail ():
    global thumbnails
    placeholder = send_file (open ("static/file-earmark-music.svg", "rb"), mimetype = "image/svg+xml")
    player = request.args.get ("player")
    if thumbnails.get (player) is None:
        return placeholder
    img = subprocess.run (["curl", "-s", thumbnails [player]], capture_output = True)
    try:
        img.check_returncode ()
    except subprocess.CalledProcessError:
        return placeholder
    kind = filetype.guess (img.stdout)
    if kind is None:
        return placeholder
    return send_file (io.BytesIO (img.stdout), mimetype = kind.mime)

@app.route ("/test-redir", methods = ["GET"])
def test_redir ():
    return redirect ("/static/file-earmark-music.svg", code = 307)

@app.route ("/", methods = ["GET"])
def index ():
    return redirect ("/static/index.html", code = 307)

if __name__ == "__main__":
    server = make_server ("0.0.0.0", 58468, app)
    logging.getLogger ("werkzeug").setLevel (logging.ERROR)
    server.serve_forever ()