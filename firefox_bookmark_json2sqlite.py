#!/usr/bin/env python3

import json

from argparse import ArgumentParser
from urllib.parse import urlparse
import sqlite3
from sqlite3 import Error
import time

SYNC_STATUS_UNKNOWN = 0
SYNC_STATUS_NEW = 1
SYNC_STATUS_NORMAL = 2

db_conn = None
db_cursor = None

bm_rowid_custom_first = 7
bm_rowid_custom_started = None

tag_root_id = 4
tag_texts_map = None

def db_connect(db_file):
    global db_conn, db_cursor

    db_conn = None
    try:
        db_conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
    db_conn.enable_load_extension(True)
    db_conn.load_extension("./sqlite-mozilla-url-hash")
    db_cursor = db_conn.cursor()


def db_query(query, values):
    db_cursor.execute(query, values)
    return db_cursor.lastrowid


def db_commit():
    db_conn.commit()


def add_tree(bm_tree):
    global bm_rowid_custom_started, tag_texts_map

    bm_rowid_custom_started = False
    tag_texts_map = {}
    add_subtree(bm_tree, 0)


def add_subtree(bm_subtree, parent_id):
    if bm_subtree["type"] == "text/x-moz-place-container":
        bookmark_id = add_bookmark(bm_subtree, parent_id, None)
        if "children" in bm_subtree:
            for one_child in bm_subtree["children"]:
                add_subtree(one_child, bookmark_id)
    elif bm_subtree["type"] == "text/x-moz-place":
        place_id = add_place(bm_subtree)
        add_bookmark(bm_subtree, parent_id, place_id)
        add_tags(bm_subtree, place_id)


def add_bookmark(item, parent_id, place_id):
    global bm_rowid_custom_started

    if item["id"] < bm_rowid_custom_first:
        rowid = item["id"]
    elif bm_rowid_custom_started:
        rowid = None
    else:
        rowid = bm_rowid_custom_first
        bm_rowid_custom_started = True
    return db_query(
        '''
            INSERT INTO moz_bookmarks(id,type,fk,parent,position,title,keyword_id,folder_type,dateAdded,lastModified,guid,syncStatus)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        ''',
        (
            rowid,
            item["typeCode"],
            place_id,
            parent_id,
            item["index"],
            item["title"],
            None,
            None,
            item["dateAdded"],
            item["lastModified"],
            item["guid"],
            SYNC_STATUS_NEW
        )
    )


def add_place(item):
    return db_query(
        '''
            INSERT INTO moz_places(url,title,rev_host,frecency,guid,foreign_count,url_hash)
            VALUES(?,?,?,?,?,?,hash(?))
        ''',
        (
            item["uri"],
            item["title"],
            urlparse(item["uri"]).netloc[::-1],
            2075,
            item["guid"] + "-P",
            1,
            item["uri"]
        )
    )


def add_tags(item, place_id):
    if not("tags" in item):
        return
    tags = set(item["tags"].split(","))
    for idx, one_tag in enumerate(tags):
        tag_text_id = add_tag_text(item, one_tag, idx)
        add_tag_link(item, place_id, tag_text_id, idx)


def add_tag_text(item, tag_text, tag_index):
    # Check if this tag has been added before
    if tag_text in tag_texts_map:
        tag_text_id = tag_texts_map[tag_text]
    else:
        # Create the tag main entry
        tag_text_id = db_query(
            '''
                INSERT INTO moz_bookmarks(id,type,fk,parent,position,title,keyword_id,folder_type,dateAdded,lastModified,guid,syncStatus)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            ''',
            (
                None,
                2,
                None,
                tag_root_id,
                0,
                tag_text,
                None,
                None,
                item["dateAdded"],
                item["lastModified"],
                item["guid"] + "-T-" + str(tag_index),
                SYNC_STATUS_NEW
            )
        )
        tag_texts_map[tag_text] = tag_text_id
    return tag_text_id


def add_tag_link(item, place_id, tag_text_id, tag_index):
        # Add the link between the tag text and the place ID
        db_query(
            '''
                INSERT INTO moz_bookmarks(id,type,fk,parent,position,title,keyword_id,folder_type,dateAdded,lastModified,guid,syncStatus)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            ''',
            (
                None,
                1,
                place_id,
                tag_text_id,
                0,
                None,
                None,
                None,
                item["dateAdded"],
                item["lastModified"],
                item["guid"] + "-" + str(tag_index) + "L",
                SYNC_STATUS_NEW
            )
        )


def current_micro_time():
    return round(time.time() * 1000000)


if __name__ == "__main__":
    argparser = ArgumentParser(description="Imports the contents of bookmarks.json to moz_bookmarks table of places.sqlite. The table is cleared, don't forget to back up!")

    argparser.add_argument(
        "in_file",
        help="Path to json bookmarks file."
    )
    argparser.add_argument(
        "out_file",
        help="Path to places.sqlite file."
    )

    parsed_args = argparser.parse_args()


with open(parsed_args.in_file, "r") as read_file:
    data = json.load(read_file)
    db_connect(parsed_args.out_file)
    db_query("DELETE FROM moz_places", ())
    db_query("DELETE FROM moz_bookmarks", ())

    # Create the root entry for the tags
    ts_now = current_micro_time()
    db_query(
        '''
            INSERT INTO moz_bookmarks(id,type,fk,parent,position,title,keyword_id,folder_type,dateAdded,lastModified,guid,syncStatus)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        ''',
        (tag_root_id,2,None,1,2,"tags",None,None,ts_now,ts_now,"tags________",SYNC_STATUS_NEW)
    )

    add_tree(data)
    db_commit()
