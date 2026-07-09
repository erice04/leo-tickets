import functools

import flask
from authlib.integrations.requests_client import OAuth2Session
import google.auth.exceptions
import google.oauth2.credentials
import googleapiclient.discovery

ACCESS_TOKEN_URI = "https://www.googleapis.com/oauth2/v4/token"
AUTHORIZATION_URL = (
    "https://accounts.google.com/o/oauth2/v2/auth?access_type=offline&prompt=consent"
)
AUTHORIZATION_SCOPE = "openid email profile"

AUTH_TOKEN_KEY = "auth_token"
AUTH_STATE_KEY = "auth_state"

bp = flask.Blueprint("google_auth", __name__)


def _client_id():
    return flask.current_app.config["GOOGLE_CLIENT_ID"]


def _client_secret():
    return flask.current_app.config["GOOGLE_CLIENT_SECRET"]


def _redirect_uri():
    return flask.current_app.config["GOOGLE_AUTH_REDIRECT_URI"]


def _base_uri():
    return flask.current_app.config["BASE_URI"]


def is_logged_in():
    return AUTH_TOKEN_KEY in flask.session


def build_credentials():
    if not is_logged_in():
        raise RuntimeError("User must be logged in")

    oauth2_tokens = flask.session[AUTH_TOKEN_KEY]
    return google.oauth2.credentials.Credentials(
        oauth2_tokens["access_token"],
        refresh_token=oauth2_tokens.get("refresh_token"),
        client_id=_client_id(),
        client_secret=_client_secret(),
        token_uri=ACCESS_TOKEN_URI,
    )


def get_user_info():
    credentials = build_credentials()
    oauth2_client = googleapiclient.discovery.build(
        "oauth2", "v2", credentials=credentials
    )
    try:
        return oauth2_client.userinfo().get().execute()
    except google.auth.exceptions.RefreshError:
        flask.session.pop(AUTH_TOKEN_KEY, None)
        flask.session.pop(AUTH_STATE_KEY, None)
        return None


def no_cache(view):
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        response = flask.make_response(view(*args, **kwargs))
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "-1"
        return response

    return wrapper


@bp.route("/google/login")
@no_cache
def login():
    session = OAuth2Session(
        _client_id(),
        _client_secret(),
        scope=AUTHORIZATION_SCOPE,
        redirect_uri=_redirect_uri(),
    )
    uri, state = session.create_authorization_url(AUTHORIZATION_URL)
    flask.session[AUTH_STATE_KEY] = state
    flask.session.permanent = True
    return flask.redirect(uri, code=302)


@bp.route("/google/auth")
@no_cache
def google_auth_redirect():
    req_state = flask.request.args.get("state", default=None, type=None)
    if req_state != flask.session.get(AUTH_STATE_KEY):
        return flask.make_response("Invalid state parameter", 401)

    session = OAuth2Session(
        _client_id(),
        _client_secret(),
        scope=AUTHORIZATION_SCOPE,
        state=flask.session[AUTH_STATE_KEY],
        redirect_uri=_redirect_uri(),
    )
    oauth2_tokens = session.fetch_token(
        ACCESS_TOKEN_URI, authorization_response=flask.request.url
    )
    flask.session[AUTH_TOKEN_KEY] = oauth2_tokens
    return flask.redirect(_base_uri(), code=302)


@bp.route("/google/logout")
@no_cache
def logout():
    flask.session.pop(AUTH_TOKEN_KEY, None)
    flask.session.pop(AUTH_STATE_KEY, None)
    return flask.redirect(_base_uri(), code=302)
