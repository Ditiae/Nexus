import re

from flask import *
import json
import csv
import mysql.connector
from mysql.connector import errorcode
import copy
import platform
import os
from loguru import logger

if platform.system() == "Linux":
	os.chdir("/var/www/nexusapi")

with open("settings.json") as f:
    SETTINGS = json.load(f)

with open("auth.csv") as f:
    rows = [row for row in csv.reader(f)]

    invalid_auth = [row[1] for row in rows if int(row[2]) == 0]
    AUTH = [row[1] for row in rows if int(row[2]) == 1]

app = Flask(__name__)


def check_auth(rf):
    if "key" not in rf:
        return error_frame("Specify an authentication key", 400)
    elif rf["key"] in invalid_auth:
        return error_frame("This authentication key was deactivated", 403)
    elif rf["key"] not in AUTH:
        return error_frame("Invalid authentication key", 403)
    else:
        return True


def connect_to_database():
    try:
        c = mysql.connector.connect(**SETTINGS["db-creds"])
    except mysql.connector.Error as e:
        if e.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            c = False
            logger.exception("MySQL - Invalid credentials")
        elif e.errno == errorcode.ER_BAD_DB_ERROR:
            c = False
            logger.exception("MySQL - Invalid database")
        else:
            c = False
            logger.exception("MySQL - Generic error")
    return c


def db_query(query, values, connection, commit=False):
    cursor = connection.cursor()
    cursor.execute(query, tuple(values))
    if commit:
        connection.commit()
    try:
        r = cursor.fetchall()
    except mysql.connector.errors.InterfaceError:
        r = []
    cursor.close()
    return r


# API helper functions
def val_strings(vals):
    value_string = ""
    mark_string = ""
    for f in vals:
        value_string += f"{f},"
        mark_string += "%s,"

    return value_string[:-1], mark_string[:-1]


def check_required(vals, inputs):
    for i in vals:
        if i not in inputs:
            return error_frame(f"{i} missing in POST", 400)
    return True


def check_float(vals, inputs):
    for i in vals:
        if inputs[i] is not None:
            try:
                float(inputs[i])
            except ValueError:
                return error_frame(f"{i} must be a floating point number", 400)
    return True


def check_integer(vals, inputs):
    for i in vals:
        if inputs[i] is not None:
            try:
                a = float(inputs[i])
                b = int(a)
            except ValueError:
                return error_frame(f"{i} must be an integer number", 400)
            else:
                return True if a == b else error_frame(f"{i} must be an integer number", 400)
    return True


def check_boolean(vals, inputs):
    for i in vals:
        if inputs[i] is not None:
            if inputs[i] not in ["0", "1"]:
                return error_frame(f"{i} can only accept 1, 0, true, false, or null", 400)
    return True


def check_json(vals, inputs):
    for i in vals:
        if inputs[i] is not None:
            try:
                json.loads(inputs[i])
            except json.decoder.JSONDecodeError:
                return error_frame(f"{i} must be valid JSON")
    return True


# standard response frames
def error_frame(e, code, show_content=False):
    if not show_content:
        jresp = {"message": e, "status": "error"}
    else:
        jresp = {"message": e, "status": "error", "content": None}

    return app.response_class(
        response=json.dumps(jresp),
        status=code,
        mimetype='application/json'
    )


def success_frame(e, code, content=None):
    if content is None:
        jresp = {"message": e, "status": "ok"}
    else:
        jresp = {"message": e, "status": "ok", "content": content}

    return app.response_class(
        response=json.dumps(jresp),
        status=code,
        mimetype='application/json'
    )


def organise_inputs(fields, values, ignore_boolean=False):
    proto = {}
    for i in fields:
        if (i not in values):
            proto[i] = None
        elif values[i].lower() == "null":
            proto[i] = None
        elif (values[i].lower() == "true") and (not ignore_boolean):
            proto[i] = "1"
        elif (values[i].lower() == "false") and (not ignore_boolean):
            proto[i] = "0"
        else:
            proto[i] = values[i]
    return proto


def validate_url(url):
    regex = re.compile(r'^(?:http|ftp)s?://(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d+)?(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None


# the below two errorhandlers are if the errors are thrown by flask, eg trying to send a GET request to a post only
# endpoint
@app.errorhandler(400)
def method_not_allowed(e):
    return error_frame("The server could not understand the request", 400)


@app.errorhandler(405)
def method_not_allowed(e):
    return error_frame("Method not allowed", 405)


@app.errorhandler(500)
def internal_server_error(e):
    return error_frame("Internal server error", 500)


# endpoints
@app.route("/")
def root():
    return error_frame("Forbidden", 403)


@app.route("/create/", methods=["POST"])
def create():
    post_args = copy.deepcopy(request.form)

    ca = check_auth(post_args)
    if ca is not True:
        return ca

    conn = connect_to_database()
    if not conn:
        return internal_server_error("")

    valid_fields = ["mod_id", "mod_name", "mod_desc", "mod_version", "file_id", "size_kb", "category_name", "adult_content", "content_preview", "uploaded_time", "external_virus_scan_url"]
    inputs = {}

    # check required fields
    cr = check_required(["mod_id", "mod_name"], post_args)
    if cr is not True:
        return cr

    # organise input values
    inputs = organise_inputs(valid_fields, post_args)

    # check integers are valid
    ci = check_integer(["file_id", "size_kb", "uploaded_time"], inputs)
    if ci is not True:
        return ci

    # check floating point numbers are valid
    cf = check_float(["mod_id"], inputs)
    if cf is not True:
        return cf

    # check booleans
    cb = check_boolean(["adult_content"], inputs)
    if cb is not True:
        return cb

    # check json validity
    cj = check_json(["content_preview"], inputs)
    if cj is not True:
        return cj

    # check if ID already exists, and if so, stop

    rows = db_query("SELECT * FROM skyrim WHERE mod_id`1`=%s", [inputs["mod_id"]], conn)

    if len(rows) != 0:
        return error_frame("An entry with that mod ID already exists", 400)

    # actually insert
    value_string, mark_string = val_strings(valid_fields)
    db_query(f"INSERT INTO skyrim ({value_string}) VALUES ({mark_string})", [inputs[val] for val in inputs], conn, commit=True)

    return success_frame("Success!", 200)


"""
@app.route("/link/add/", methods=["POST"])
def link_add():
    post_args = copy.deepcopy((request.form))

    ca = check_auth(post_args)
    if ca is not True:
        return ca

    conn = connect_to_database()
    if not conn:
        return internal_server_error("")

    valid_fields = ["mod_id, "download_url"]

    cr = check_required(valid_fields, post_args)
    if cr is not True:
        return cr

    inputs = organise_inputs(valid_fields, post_args)

    cf = check_float(["mod_id], inputs)
    if cf is not True:
        return cf

    vu = validate_url(str(inputs["download_url"]))
    if not vu:
        return error_frame("download_url must be a valid URL and must not refrence localhost", 400)

    # insert into
    value_string, mark_string = val_strings(valid_fields)
    db_query(f"REPLACE INTO skyrim_downloads ({value_string}) VALUES ({mark_string})", [inputs[val] for val in inputs], conn, commit=True)

    return success_frame("Success!", 201)


@app.route("/link/remove/", methods=["POST"])
def link_remove():
    post_args = copy.deepcopy(request.form)

    ca = check_auth(post_args)
    if ca is not True:
        return ca

    conn = connect_to_database()
    if not conn:
        return internal_server_error("")

    valid_fields = ["mod_id]

    cr = check_required(valid_fields, post_args)
    if cr is not True:
        return cr

    inputs = organise_inputs(valid_fields, post_args)

    cf = check_float(valid_fields, inputs)
    if cf is not True:
        return cf

    # check if an entry exists with the specified mod
    rows = db_query("SELECT count(*) as count FROM skyrim_downloads WHERE mod_id = %s", [inputs["mod_id]], conn)

    for row in rows:
        if row[0] == 0:
            return error_frame("No entry exists with specified ID", 404)

    # make actual query
    db_query("DELETE FROM skyrim_downloads WHERE mod_id = %s LIMIT 1", [inputs["mod_id]], conn, commit=True)

    return success_frame("Success!", 200)


@app.route("/link/select/", methods=["POST"])
def link_select():
    post_args = copy.deepcopy(request.form)

    ca = check_auth(post_args)
    if ca is not True:
        return ca

    conn = connect_to_database()
    if not conn:
        return internal_server_error("")

    rows = db_query("SELECT skyrim_downloads.*, skyrim.mod_name, skyrim.mod_version, skyrim.file_id FROM skyrim_downloads "
                 "JOIN skyrim ON skyrim.mod_id = skyrim_downloads.mod_id LIMIT 1", [], conn)

    if len(rows) == 0:
        return error_frame("No rows exist in database", 404, show_content=True)
    else:
        content = {}
        content["mod_id] = rows[0][0]
        content["download_url"] = rows[0][1]
        content["mod_name"] = rows[0][2]
        content["mod_version"] = rows[0][3]
        content["file_id"] = rows[0][4]

        return success_frame("Success!", 200, content=content)
"""


@app.route("/select/", methods=["POST"])
def select():
    post_args = copy.deepcopy(request.form)

    ca = check_auth(post_args)
    if ca is not True:
        return ca

    conn = connect_to_database()
    if not conn:
        return internal_server_error("")

    valid_fields = ["mod_id"]

    cr = check_required(valid_fields, post_args)
    if cr is not True:
        return cr

    cf = check_float(["mod_id"], post_args)
    if cf is not True:
        return cf


    rows = db_query("SELECT mod_id, file_id, category_name FROM skyrim WHERE mod_id = %s", [post_args["mod_id"]], conn, commit=True)

    if len(rows) == 0:
        return error_frame("No rows exist in database", 404, show_content=True)
    else:
        content = {}

        content["mod_id"] = rows[0][0]
        content["file_id"] = rows[0][1]
        content["category_name"] = rows[0][2]

        return success_frame("Success!", 200, content=content)


@app.route("/update/", methods=["POST"])
def update():
    post_args = copy.deepcopy(request.form)

    ca = check_auth(post_args)
    if ca is not True:
        return ca

    conn = connect_to_database()
    if not conn:
        return internal_server_error("")

    valid_fields = ["mod_id", "mod_name", "mod_desc", "mod_version", "file_id", "size_kb", "category_name", "adult_content", "content_preview", "uploaded_time", "external_virus_scan_url"]
    allowable_categories = ["NOT FOUND", "HIDDEN MOD", "NO FILES", "NOT PUBLISHED", "UNDER MODERATION", "NON"]

    cr = check_required(["mod_id"], post_args)
    if cr is not True:
        return cr

    inputs = organise_inputs(valid_fields, post_args)

    ci = check_integer(["file_id", "size_kb", "uploaded_time"], inputs)
    if ci is not True:
        return ci

    cb = check_boolean(["adult_content"], inputs)
    if cb is not True:
        return cb

    cf = check_float(["mod_id"], inputs)
    if cf is not True:
        return cf

    cj = check_json(["content_preview"], inputs)
    if cj is not True:
        return cf

    # check if ID already exists, and if so, determine if it's got one of the required categories for update
    rows = db_query("SELECT category_name FROM skyrim WHERE mod_id=%s", [inputs["mod_id"]], conn)

    if len(rows) == 0:
        return error_frame("No entry with that mod_id exists.", 404)
    elif rows[0][0] not in allowable_categories:
        return error_frame("The entry has been found, but the category name does not allow updates to that row", 400)

    value_string, mark_string = val_strings(valid_fields)
    db_query(f"REPLACE INTO skyrim ({value_string}) VALUES ({mark_string})", [inputs[val] for val in inputs], conn, commit=True)

    return success_frame("Success!", 200)


def dl_prog_comp_combi(type):
    # Combo function for dl_progress and dl_copmleted
    # type should be either "progress" or "completed"

    post_args = copy.deepcopy(request.form)

    ca = check_auth(post_args)
    if ca is not True:
        return ca

    conn = connect_to_database()
    if not conn:
        return internal_server_error("")

    if type == "completed":  # not required for progress
        valid_fields = ["mod_id", "state"]

        cr = check_required(valid_fields, post_args)
        if cr is not True:
            return cr

        inputs = organise_inputs(valid_fields, post_args)

        cb = check_boolean(["state"], inputs)
        if cb is not True:
            return cb

        cf = check_float(["mod_id"], inputs)
        if cf is not True:
            return cf

        # Check specified mod exists
        rows = db_query("SELECT count(*) as count FROM skyrim WHERE mod_id = %s", [inputs["mod_id"]], conn)
        for row in rows:
            if row[0] == 0:
                return error_frame("No entry exists with specified ID", 404)

    # modify row
    if type == "progress":

        query = """
        SET @modid = (SELECT mod_id FROM skyrim WHERE dl_progress = 0 AND dl_completed = 0 LIMIT 1);
        SET @fileid = (SELECT file_id from skyrim WHERE mod_id = @modid);
        UPDATE skyrim SET dl_progress = 1 WHERE mod_id = @modid;
        SELECT @modid AS mod_id, @fileid AS file_id, mod_name, mod_version FROM skyrim WHERE mod_id=@modid;
        """

        cursor = conn.cursor()
        try:
            for i in cursor.execute(query, tuple, multi=True):
                one = i.fetchone()
                if one is not None:
                    row = one
                    break
            conn.commit()
        except RuntimeError:
            row = (None, None, None, None)

        cursor.close()

        if row == (None, None, None, None):
            return error_frame("None to download", 404, show_content=True)

        return success_frame("Success!", 200, content={
            "mod_id": row[0],
            "file_id": row[1],
            "mod_name": row[2],
            "mod_version": row[3]
        })

    elif type == "completed":
        query = "UPDATE skyrim SET dl_completed = %s WHERE mod_id = %s"
        db_query(query, [inputs["state"], inputs["mod_id"]], conn, commit=True)
    else:
        return error_frame("Internal server error", 500)


    return success_frame("Success!", 200)


@app.route("/dl/progress/", methods=["POST"])
def dl_progress():
    return dl_prog_comp_combi("progress")


@app.route("/dl/completed/", methods=["POST"])
def dl_completed():
    return dl_prog_comp_combi("completed")
