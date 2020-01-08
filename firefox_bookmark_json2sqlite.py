#!/usr/bin/env python3

import json

from argparse import ArgumentParser
from urllib.parse import urlparse
import sqlite3
from sqlite3 import Error


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
    conn.load_extension("./sqlite-mozilla-url-hash")
    return conn


def dict_generator(indict, pre="0"):
    if isinstance(indict, dict):
        indict.update({"parent":pre})
        if indict['type'] == 'text/x-moz-place-container' and 'children' in indict:
            for d in dict_generator(indict['children'], indict['id']):
                yield d
            indict.pop('children')
        yield indict

    elif isinstance(indict, list):
        for v in indict:
            for d in dict_generator(v, pre):
                yield d
            
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
    conn = create_connection(parsed_args.out_file)
    cur = conn.cursor()
    query = "DELETE FROM moz_places"
    cur.execute(query)
    query = "DELETE FROM moz_bookmarks"
    cur.execute(query)
    
    for item in dict_generator(data):
        if item['type'] == "text/x-moz-place":
            rev_host = urlparse(item["uri"]).netloc[::-1]
            newguid = item["guid"][:-1] + 'P'
            query = '''
                INSERT INTO moz_places(url,title,rev_host,frecency,guid,foreign_count,url_hash)
              VALUES(?,?,?,?,?,?,hash(?))
                '''
            cur.execute(query, (item["uri"],item["title"],rev_host,2075,newguid,1,item["uri"]))
            rowid = cur.lastrowid
            
            query = '''
                INSERT INTO moz_bookmarks(id,type,fk,parent,title,dateAdded,lastModified,guid,syncStatus)
              VALUES(?,?,?,?,?,?,?,?,?)
              '''
            cur.execute(query, (item["id"],"1",rowid,item["parent"],item["title"],item["dateAdded"],item["lastModified"],item["guid"],1)) 
            
        if item['type'] == "text/x-moz-place-container":
            query = '''
                INSERT INTO moz_bookmarks(id,type,parent,title,dateAdded,lastModified,guid,syncStatus)
              VALUES(?,?,?,?,?,?,?,?)
              '''
            cur.execute(query, (item["id"],"2",item["parent"],item["title"],item["dateAdded"],item["lastModified"],item["guid"],1)) 
            
        conn.commit()
