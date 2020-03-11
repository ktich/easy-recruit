import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps

# for file uploads
    # NOTE: put capital version -- PDF in here in case
ALLOWED_EXTENSIONS = set(['pdf', 'PDF'])

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/user")
        return f(*args, **kwargs)
    return decorated_function

def userorstafflogin_required(f):
    """
    Decorate routes to require login.
    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    Trying to allow a route for either applicants or staff logged in.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logged_in = session.get("staff_id") or session.get("user_id")
        if logged_in is None:
            return redirect("/user")
        return f(*args, **kwargs)
    return decorated_function

def stafflogin_required(f):
    """
    Decorate routes to require login.
    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("staff_id") is None:
            return redirect("/user")
        return f(*args, **kwargs)
    return decorated_function

def lookup(symbol):
    """Look up quote for symbol."""

    # Contact API
    try:
        response = requests.get(f"https://api.iextrading.com/1.0/stock/{urllib.parse.quote_plus(symbol)}/quote")
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        return {
            "name": quote["companyName"],
            "price": float(quote["latestPrice"]),
            "symbol": quote["symbol"]
        }
    except (KeyError, TypeError, ValueError):
        return None

#won't need this for final -- DELETE
def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"

# function to make sure only allowed filenames are used//never trust user (got this from: http://flask.pocoo.org/docs/1.0/patterns/fileuploads/#uploading-files)
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
