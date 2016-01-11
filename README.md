# anki-http-server
An Anki add-on that launches an HTTP server upon startup and exposes Anki's data via a REST-ish API

# Status

- Work in progress.
- Quick and dirty hack.
- It works but I don't love the code.

# Motivation

I needed a way to use Alfred on OS X to add notes to Anki. Mucking around with Anki's sqlite database directly didn't sound appealing. A lightweight HTTP server, on the other hand, opens a lot of possibilities. (ClojureScript frontend for Anki, anyone?)

The Alfred extension can be found [here](https://github.com/pbkhrv/alfred-anki-add-note).

# Installation

Copy the contents of `src` to your Anki's add-on folder (without the `src` folder itself). The code has no external dependencies.

By default listens on port 41837. To change it, edit `anki_http_server_init.py` - it'll be obvious.

# API

Only 3 endpoints for now:

### GET /decks

Returns names of all Anki decks in a json object with key 'decks':

```
{
    "decks": [
        "Python cheatsheets",
        "Clojure study"
    ]
}
```

## GET /models

Returns names of all Anki note models in a json object with key 'models':

```
{
    "models": [
        "Basic (optional reversed card)",
        "Cloze",
        "Basic",
        "Basic (and reversed card)"
    ]
}
```

### POST /decks/:deckName

Creates a "basic" note in the deck with the given deckName. Expects a urlencoded body with 2 params: `front` and `back` for the two sides of the note. Returns something meaningless.

## More!!!

No time right now, but it's easy to add more. Look at the bottom of `__init__.py`

The endpoints I really want to add:
- /notes
- /notes/:id
- A more flexible `POST /decks` that accepts the name of the note model and dynamically extracts necessary fields based on fields defined in the said model

