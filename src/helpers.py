__license__ = "Apache 2"
from streamlit.report_thread import get_report_ctx
from streamlit.hashing import _CodeHasher
from streamlit.server.server import Server

import requests
import datetime
import json
import socket
import sqlite3
import uuid


class _SessionState:
    def __init__(self, session, hash_funcs):
        """Initialize SessionState instance."""
        self.__dict__["_state"] = {
            "data": {},
            "hash": None,
            "hasher": _CodeHasher(hash_funcs),
            "is_rerun": False,
            "session": session,
        }

    def __call__(self, **kwargs):
        """Initialize state data once."""
        for item, value in kwargs.items():
            if item not in self._state["data"]:
                self._state["data"][item] = value

    def __getitem__(self, item):
        """Return a saved state value, None if item is undefined."""
        return self._state["data"].get(item, None)
        
    def __getattr__(self, item):
        """Return a saved state value, None if item is undefined."""
        return self._state["data"].get(item, None)

    def __setitem__(self, item, value):
        """Set state value."""
        self._state["data"][item] = value

    def __setattr__(self, item, value):
        """Set state value."""
        self._state["data"][item] = value
    
    def clear(self):
        """Clear session state and request a rerun."""
        self._state["data"].clear()
        self._state["session"].request_rerun()
    
    def sync(self):
        """Rerun the app with all state values up to date from the beginning to fix rollbacks."""

        # Ensure to rerun only once to avoid infinite loops
        # caused by a constantly changing state value at each run.
        #
        # Example: state.value += 1
        if self._state["is_rerun"]:
            self._state["is_rerun"] = False
        
        elif self._state["hash"] is not None:
            if self._state["hash"] != self._state["hasher"].to_bytes(self._state["data"], None):
                self._state["is_rerun"] = True
                self._state["session"].request_rerun()

        self._state["hash"] = self._state["hasher"].to_bytes(self._state["data"], None)
        
        
def _get_session():
    session_id = get_report_ctx().session_id
    session_info = Server.get_current()._get_session_info(session_id)

    if session_info is None:
        raise RuntimeError("Couldn't get your Streamlit Session object.")
    
    return session_info.session

def get_title(druid: str) -> str:
    con = sqlite3.connect("data/druid_fast.sqlite")
    cur = con.cursor()
    cur.execute("SELECT title FROM Druids WHERE druid=?", (druid,))
    result = cur.fetchone()
    if result is not None:
        return result[0]

def save_fast_to_druid(druid: str, fast_uris: list):
    if len(fast_uris) < 1:
        return
    host_name = socket.gethostname()
    firebase_url = f'https://bio-etd-fast.firebaseio.com/{uuid.uuid4()}.json'
    data = {
        "druid": druid,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "fast_uris": fast_uris,
        "ip": socket.gethostbyname(host_name)
    }
    print(firebase_url)
    result = requests.post(firebase_url, data=json.dumps(data))
    if result.status_code < 400:
        return True
