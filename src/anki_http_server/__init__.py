from __future__ import print_function
import json
import threading
import os
import anki
import aqt
from aqt.qt import QObject, SIGNAL

# True = allow duplicate notes to be added
ALLOW_DUPLICATES = False

# HACK
writeLog = print

# Borrowed from Rikaisama anki add-on
# http://rikaisama.sourceforge.net/#realtime_import_help
#
# Technically, this doesn't need to be a class since it doesn't have properties.
# Might make sense to move it into a module.
class Anki:
    def addNote(self, deckName, modelName, fields, tags=list()):
        note = self.createNote(deckName, modelName, fields, tags)
        if note is not None:
            collection = self.collection()
            self.window().checkpoint("Add Note from Real-Time Import")
            collection.addNote(note)
            collection.autosave()
            writeLog("Note added.")
            self.stopEditing()
            return note.id

    def canAddNote(self, deckName, modelName, fields):
        return bool(self.createNote(deckName, modelName, fields))

    def createNote(self, deckName, modelName, fields, tags=list()):
        model = self.models().byName(modelName)
        if model is None:
            return None

        deck = self.decks().byName(deckName)
        if deck is None:
            return None

        note = anki.notes.Note(self.collection(), model)
        note.model()['did'] = deck['id']
        note.tags = tags

        try:
            for name, value in fields.items():
                note[name] = value
        except:
            #showTooltip("Error, current note type does not contain the following field: '" + name + "'", 5000);
            writeLog("Anki.createNote: Error, current note type does not contain the following field: '" + name + "'")
            return None

        dupOrEmpty = note.dupeOrEmpty()

        if dupOrEmpty == 1:
            #showTooltip("Error, first field in note is empty!");
            writeLog("Anki.createNote: first field in note is empty!")
            return note
        elif dupOrEmpty == 2 and not ALLOW_DUPLICATES:
            #showTooltip("Error, duplicate note!");
            writeLog("Anki.createNote: Error, duplicate note!")
        else:
            return note

    def browseNote(self, noteId):
        browser = aqt.dialogs.open('Browser', self.window())
        browser.form.searchEdit.lineEdit().setText('nid:{0}'.format(noteId))
        browser.onSearch()

    def startEditing(self):
        self.window().requireReset()

    def stopEditing(self):
        if self.collection():
            self.window().maybeReset()

    def window(self):
        return aqt.mw

    def addUiAction(self, action):
        self.window().form.menuTools.addAction(action)

    def collection(self):
        return self.window().col

    def models(self):
        return self.collection().models

    def modelNames(self):
        return self.models().allNames()

    def modelFieldNames(self, modelName):
        model = self.models().byName(modelName)
        if model is not None:
            return [field['name'] for field in model['flds']]

    def decks(self):
        return self.collection().decks

    def deckNames(self):
        return self.decks().allNames()

    def curModelID(self):
        return self.collection().conf['curModel']

    def curDeckID(self):
        return self.collection().conf['curDeck']

    def curModel(self):
        return self.models().get(self.curModelID())

    def curDeck(self):
        return self.decks().get(self.curDeckID())

    def curModelName(self):
        return self.curModel()['name']

    def curDeckName(self):
        return self.curDeck()['name']

# Needed because web server runs in its own thread
# but sqlite object lives in the main thread.
# Using an event queue and an event processor that's tied to
# the main thread solves that problem.
# More here: http://pyqt.sourceforge.net/Docs/PyQt4/qobject.html#thread-affinity
class EventQueue(QObject):
    def newNote(self, deckName, modelName, fields):
        self.emit(SIGNAL("event"), 'newNote', deckName, modelName, fields)

class EventProcessor(QObject):
    def __init__(self, queue, ank):
        self.queue = queue
        self.connect(queue, SIGNAL("event"), self.onEvent)
        self.ank = ank

    def onEvent(self, evt, *args):
        if evt == 'newNote':
            deckName = args[0]
            modelName = args[1]
            fields = args[2]
            self.ank.addNote(deckName, modelName, fields)

# Weirdness around where python modules are loaded from under Anki
def patch_pythonpath():
    old_ppath = os.environ.get('PYTHONPATH') or ''
    path = old_ppath.split(os.path.pathsep)
    thisdir = os.path.dirname(__file__)
    new_path = os.path.pathsep.join([thisdir] + path)
    print(new_path)
    os.environ['PYTHONPATH'] = new_path

patch_pythonpath()

from itty import get, post, run_itty, Response

eventQueue = EventQueue()
eventProcessor = EventProcessor(eventQueue, Anki())

# Finally, the API

@get('/decks')
def get_decks(request):
    a = Anki()
    return Response(json.dumps({'decks': a.deckNames()}), content_type='application/json')

@get('/models')
def get_models(request):
    a = Anki()
    return Response(json.dumps({'models': a.modelNames()}), content_type='application/json')

@post('/decks/(?P<name>\w+)')
def add_note_to_deck(request, name):
    front = request.POST.get('front', 'missing front')
    back = request.POST.get('back', 'missing back')
    eventQueue.newNote(name, 'Basic', {'Front': front, 'Back': back})
    return Response(json.dumps({'status': 'ok'}), content_type='application/json')

def init(port):
    def itty_server_thread():
        run_itty(host='127.0.0.1', port=port)
    t = threading.Thread(target=itty_server_thread)
    t.daemon = True
    t.start()
