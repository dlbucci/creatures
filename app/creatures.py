#!/usr/bin/env python

##
# Creatures.Bucci.Sexy
##
import mimetypes, os, sys, traceback
from string import Template
from cgi import escape, FieldStorage
import config

def index(env, start_response):
    body = ["<span class='img-wrapper'><img src='/images/%s' /><div class='img-hover'></div></span>"%(image) for image in sorted(os.listdir("images"))]
    with open("app/templates/index.html", "r") as f:
        return rebase(start_response, Template(f.read()).substitute(dict(images="".join(body))))

def new(env, start_response):
    with open("app/templates/new.html", "r") as f:
        return rebase(start_response, f.read())

def create(env, start_response):
    body = parse_post_body(env)
    if "images" not in body:
        return ["YOU NEED TO UPLOAD IMAGES, DICKHEAD!"]
    if "password" not in body:
        return ["ENTER A PASSWORD, PAL!"]
    password = body["password"].value
    if password != config.PWD:
        return ["FORBIDDEN"]
    images = body["images"]
    if not isinstance(images, list):
        images = [images]
    for image in images:
        if not image.file or not image.filename:
            continue
        with open("images/%s"%(image.filename), "w") as f:
            f.write(image.file.read())
    return redirect("/new", start_response)

def env(env, start_response):
    env = ["%s: %s" % (key, value) for key, value in sorted(env.items())]
    with open("app/templates/env.html", "r") as f:
        return rebase(start_response, Template(f.read()).substitute(dict(env="\n".join(env))))

def send_file(start_response, filepath):
    with open(filepath, "r") as f:
        (mimetype, encoding) = mimetypes.guess_type(filepath)
        start_response("200 OK", [("Content-Type", mimetype)])
        return [f.read()]
    start_response("404 Not Found", [("Content-Type", "text/plain")])
    return [""]

def parse_post_body(env):
    post_env = env.copy()
    post_env["QUERY_STRING"] = ""
    return FieldStorage(
        fp=env["wsgi.input"],
        environ=post_env,
        keep_blank_values=True)

def print_error(start_response):
    start_response("500 Internal Server Error", [("Content-Type", "text/html")])
    body = "<pre>%s</pre>" % (traceback.format_exc())
    with open("app/templates/_layout.html", "r") as f:
        return [Template(f.read()).substitute(dict(body=body, title="ERROR"))]

def rebase(start_response, body, title="Creatures By Daniel Bucci"):
    start_response("200 OK", [("Content-Type", "text/html")])
    with open("app/templates/_layout.html", "r") as f:
        return [Template(f.read()).substitute(dict(body=body, title=title))]

def redirect(location, start_response):
    start_response("302 Found", [("Location", location)])
    return ["1"]

routes = {
    "GET /": index,
    "GET /new": new,
    "POST /": create,
    "GET /env": env
}
static_dirs = {
    "images": "/images/",
    "static": "/"
}

def application(env, start_response):
    req_met = env.get("REQUEST_METHOD")
    req_uri = env.get("REQUEST_URI")
    route = routes.get("%s %s"%(req_met, "/"+req_uri.split("/")[1]))
    if route:
        try:
            return route(env, start_response)
        except:
            return print_error(start_response)
    elif req_met == "GET":
        for directory, prefix in static_dirs.iteritems():
            if not req_uri.startswith(prefix):
                continue
            filepath = os.path.join(directory, req_uri[len(prefix):]) 
            if os.path.isfile(filepath):
                return send_file(start_response, filepath)
    start_response("404 Not Found", [("Content-Type", "text/plain")])
    return ["Not Found"]

