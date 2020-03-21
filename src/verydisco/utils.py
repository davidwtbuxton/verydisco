import json
import urllib.parse
import urllib.request


URL_SCHEMES = ("http", "https")


def load_location(loc: str) -> dict:
    """Read a URL or filename as JSON."""
    parts = urllib.parse.urlparse(loc)

    if parts.scheme in URL_SCHEMES:
        doc = load_url(loc)
    else:
        doc = load_filename(loc)

    return doc


def load_url(loc: str) -> dict:
    """Fetch an URL, parse it as JSON."""
    with urllib.request.urlopen(loc) as response:
        return json.load(response)


def load_filename(loc: str) -> dict:
    """Open a filename, parse it as JSON."""
    with open(loc) as fh:
        return json.load(fh)
