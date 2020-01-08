# Project Title

**firefox_bookmark_json2sqlite** - JSON to Sqlite bookmarks importer for Mozilla Firefox

# Project Description

A very simple tool for importing bookmarks.json to Firefox places.sqlite database.

For some reason i could not import my saved bookmarks using built-in Firefox imported. I was receiving `"Unable to process the backup file."` with `"UNIQUE constraint failed: moz_bookmarks.guid"` message in the browser console, that's why i had to import them manually. I am totally not sure if this tool does everything correctly and fills up all the fields in a proper way, but it worked at least in my case. Tested on Firefox 68.2.0esr.

Also i was too lazy to deal with old data kept in moz_places and moz_bookmarks tables and their relations, so they are cleared before importing! Be sure that you have everything backed up. My proposal would be to create an empty Firefox profile, import your bookmarks there, and then merge them using Firefox Sync or other merging tool.

## Getting Started

### Prerequisites

The script uses *sqlite-mozilla-url-hash.so* plugin which generates Mozilla URL hashes for Sqlite. Download and compile it from *https://github.com/bencaradocdavies/sqlite-mozilla-url-hash.git* and put the library to the folder where you run script from.

### Running

Download:

`wget https://raw.githubusercontent.com/Vshmuk/sqlite-mozilla-url-hash/master/firefox_bookmark_json2sqlite.py`

and run:

`./firefox_bookmark_json2sqlite.py bookmarks.json places.sqlite`

## Built With

* [The Mozilla urlhash Sqlite library](https://github.com/bencaradocdavies/sqlite-mozilla-url-hash.git)

## Authors

* **Evgeny Beysembaev** - *Initial work* - [Vshmuk](https://github.com/Vshmuk)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

