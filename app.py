# Built-in modules:
import io, json, logging, re, subprocess
from base64 import b64decode
from datetime import datetime
from hashlib import sha256
from html import unescape
from urllib.parse import unquote

# Third-party modules:
from flask import Flask, redirect, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.serving import make_server
import filetype, jsonschema

app = Flask (__name__)
CORS (app)
thumbnails, thumb_files = {}, {}

with open ("control_schema.json") as f:
    control_schema = json.load (f)
mpris_keys = ["playerInstance", "position", "mpris:length", "status", "volume", "shuffle", "loop", "title", "artist", "xesam:album", "mpris:artUrl"]

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
    global control_schema, mpris_keys, thumb_files, thumbnails
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

    return_args = run_playerctl (["playerctl", "-a", "metadata", "-f", "{{markup_escape(" + ")}}'{{markup_escape(".join (mpris_keys) + ")}}"])
    if isinstance (return_args, tuple):
        return return_args

    thumbnails = {}
    resp = {
        "__timestamp__": datetime.now ().timestamp (),
        "players": []
    }
    default = lambda x: None if x == "" else unescape (x)
    for player in return_args.stdout.decode ("utf-8").strip ().split ("\n"):
        values = player.split ("'")
        resp ["players"].append ({
            "playerInstance": default (values [0]),
            "position": int (values [1] or 0) / 1000000, # Microseconds to seconds
            "length": int (values [2] or 0) / 1000000,
            "status": default (values [3]),
            "volume": float (values [4]),
            "shuffle": default (values [5]),
            "loop": default (values [6]),
            "title": default (values [7]),
            "artist": default (values [8]),
            "album": default (values [9]),
        })
        thumbnails [default (values [0])] = default (values [-1]) or None
    for i in thumb_files.copy ():
        if i not in thumbnails:
            del thumb_files [i]
    return jsonify (resp)

@app.route ("/thumbnail", methods = ["GET"])
def thumbnail ():
    global thumbnails, thumb_files
    placeholder = "/static/file-earmark-music.svg"
    thumb_hash = request.args.get ("hash")
    if thumb_hash is not None:
        for i in thumb_files.values ():
            if i [0] == thumb_hash:
                kind = filetype.guess (i [1])
                return send_file (io.BytesIO (i [1]), mimetype = kind.mime)
        return send_file ("static/file-earmark-music.svg", mimetype = "image/svg+xml")

    resp = {}
    for player, uri in thumbnails.items ():
        if uri is None:
            resp [player] = placeholder
            continue
        if re.fullmatch (r"file:\/\/\/[^\/]+", uri): # File URI
            try:
                with open (uri [7 : ], "rb") as f:
                    img = f.read ()
            except FileNotFoundError:
                resp [player] = placeholder
                continue
        elif re.fullmatch (r"data:image([^;]*);base64,(.+)", uri): # Data URI in base64
            img = b64decode (uri.split (",", 1) [1])
        elif re.fullmatch (r"data:image([^;]*),(.+)", uri): # Data URI in percent encoding (should not happen)
            uri = unquote (uri.split (",", 1) [1])
            img = bytes (unquote (uri), "utf-8")
        else: # use curl as fallback
            img = subprocess.run (["curl", "-s", uri], capture_output = True)
            try:
                img.check_returncode ()
            except subprocess.CalledProcessError:
                resp [player] = placeholder
                continue
            img = img.stdout
        thumb_hash = sha256 (img).hexdigest ()
        thumb_files [player] = (thumb_hash, img)
        resp [player] = f"/thumbnail?hash={thumb_hash}"
    return jsonify (resp)

@app.route ("/", methods = ["GET"])
def index ():
    return redirect ("/static/index.html", code = 307)

if __name__ == "__main__":
    server = make_server ("0.0.0.0", 58468, app)
    logging.getLogger ("werkzeug").setLevel (logging.ERROR)
    server.serve_forever ()