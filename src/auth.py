from __future__ import absolute_import
import os
import flask
from authlib.integrations.requests_client import OAuth2Session

from flask import url_for
from urllib.parse import urlencode, urljoin

from requests import request
from abc import ABCMeta, abstractmethod
from six import iteritems, add_metaclass

COOKIE_EXPIRY = 60 * 60 * 24 * 14
COOKIE_AUTH_USER_NAME = 'AUTH-USER'
COOKIE_AUTH_ACCESS_TOKEN = 'AUTH-TOKEN'

AUTH_STATE_KEY = 'auth_state'

CLIENT_ID = os.environ.get('AUTH0_CLIENT_ID')
CLIENT_SECRET = os.environ.get('AUTH0_CLIENT_SECRET')
DOMAIN = os.environ.get('AUTH0_DOMAIN')
LOGOUT_URL = f'https://{DOMAIN}/v2/logout'
AUTH_REDIRECT_URI = '/login/callback'

# Auth0 URLs
AUTH_URL = f'https://{DOMAIN}/authorize'
AUTH_TOKEN_URI = f'https://{DOMAIN}/oauth/token'
AUTH_USER_INFO_URL = f'https://{DOMAIN}/userinfo'

# Update callback URL with publicly accessible URL
# If running locally, you may need to use localhost or your machine's IP
FIXED_CALLBACK_URL = os.environ.get('AUTH0_CALLBACK_URL', 'http://localhost:8050/login/callback')

AUTH_FLASK_ROUTES = os.environ.get('AUTH_FLASK_ROUTES',"false")
if AUTH_FLASK_ROUTES == "true":
    AUTH_FLASK_ROUTES = True
elif AUTH_FLASK_ROUTES == "false":
    AUTH_FLASK_ROUTES = False
else:
    print(f"warning: AUTH_FLASK_ROUTES is set to {AUTH_FLASK_ROUTES}. Must be 'true' or 'false', otherwise will raise this warning and be set to False.")
    AUTH_FLASK_ROUTES = False


@add_metaclass(ABCMeta)
class Auth(object):
    def __init__(self, app, authorization_hook=None, _overwrite_index=True):
        self.app = app
        self._index_view_name = app.config['routes_pathname_prefix']
        if _overwrite_index:
            self._overwrite_index()
            self._protect_views()
        self._index_view_name = app.config['routes_pathname_prefix']
        self._auth_hooks = [authorization_hook] if authorization_hook else []

    def _overwrite_index(self):
        original_index = self.app.server.view_functions[self._index_view_name]

        self.app.server.view_functions[self._index_view_name] = \
            self.index_auth_wrapper(original_index)

    def _protect_views(self):
        # TODO - allow users to white list in case they add their own views
        for view_name, view_method in iteritems(
                self.app.server.view_functions):
            if view_name != self._index_view_name:
                self.app.server.view_functions[view_name] = \
                    self.auth_wrapper(view_method)

    def is_authorized_hook(self, func):
        self._auth_hooks.append(func)
        return func

    @abstractmethod
    def is_authorized(self):
        pass

    @abstractmethod
    def auth_wrapper(self, f):
        pass

    @abstractmethod
    def index_auth_wrapper(self, f):
        pass

    @abstractmethod
    def login_request(self):
        pass


class Auth0Auth(Auth):
    def __init__(self, app):
        Auth.__init__(self, app)
        app.server.config['SECRET_KEY'] = os.environ.get('APP_SECRET_KEY')
        app.server.config['SESSION_TYPE'] = 'filesystem'

        @app.server.route('/login/callback')
        def callback():
            return self.login_callback()

        @app.server.route('/logout/')
        def logout():
            return self.logout()

    def is_authorized(self):
        user = flask.request.cookies.get(COOKIE_AUTH_USER_NAME)
        token = flask.request.cookies.get(COOKIE_AUTH_ACCESS_TOKEN)
        if not user or not token:
            return False
        return flask.session.get(user) == token

    def login_request(self):
        # Use fixed callback URL instead of dynamic one
        redirect_uri = FIXED_CALLBACK_URL

        session = OAuth2Session(
            CLIENT_ID,
            CLIENT_SECRET,
            scope='openid profile',  # Simplified scope
            redirect_uri=redirect_uri
        )

        uri, state = session.create_authorization_url(
            AUTH_URL,
            audience=None  # Remove specific audience to fix access_denied error
        )

        flask.session['REDIRECT_URL'] = flask.request.url
        flask.session[AUTH_STATE_KEY] = state
        flask.session.permanent = False

        return flask.redirect(uri, code=302)

    def auth_wrapper(self, f):
        def wrap(*args, **kwargs):
            if AUTH_FLASK_ROUTES:
                if not self.is_authorized():
                    return flask.Response(status=403)
            response = f(*args, **kwargs)
            return response

        return wrap

    def index_auth_wrapper(self, original_index):
        def wrap(*args, **kwargs):
            if self.is_authorized():
                return original_index(*args, **kwargs)
            else:
                return self.login_request()
        return wrap

    def login_callback(self):
        if 'error' in flask.request.args:
            error_desc = flask.request.args.get('error_description', 'Unknown error')
            error_type = flask.request.args.get('error', 'Unknown')
            print(f"Auth0 Error: {error_type} - {error_desc}")
            if flask.request.args.get('error') == 'access_denied':
                return f'Authorization failed: {error_desc}'
            return f'Error encountered: {error_desc}'

        if 'code' not in flask.request.args and 'state' not in flask.request.args:
            return self.login_request()
        else:
            # user is successfully authenticated
            try:
                auth0 = self.__get_auth(state=flask.session[AUTH_STATE_KEY])
                try:
                    token = auth0.fetch_token(
                        AUTH_TOKEN_URI,
                        client_secret=CLIENT_SECRET,
                        authorization_response=flask.request.url
                    )
                    print("Token received successfully")
                except Exception as e:
                    print(f"Token fetch error: {str(e)}")
                    return f"Error fetching token: {str(e)}"

                auth0 = self.__get_auth(token=token)
                resp = auth0.get(AUTH_USER_INFO_URL)
                if resp.status_code == 200:
                    user_data = resp.json()
                    print(f"User info received: {user_data.get('name', 'Unknown')}")
                    r = flask.redirect(flask.session.get('REDIRECT_URL', '/'))
                    r.set_cookie(COOKIE_AUTH_USER_NAME, user_data.get('name', 'user'), max_age=COOKIE_EXPIRY)
                    r.set_cookie(COOKIE_AUTH_ACCESS_TOKEN, token['access_token'], max_age=COOKIE_EXPIRY)
                    flask.session[user_data.get('name', 'user')] = token['access_token']
                    return r
                else:
                    print(f"User info error: {resp.status_code} - {resp.text}")
                    return f'Could not fetch user information. Status: {resp.status_code}'
            except Exception as e:
                print(f"Callback general error: {str(e)}")
                return f'Authentication error: {str(e)}'

    @staticmethod
    def __get_auth(state=None, token=None):
        if token:
            return OAuth2Session(CLIENT_ID, token=token)
        if state:
            return OAuth2Session(
                CLIENT_ID,
                state=state,
                redirect_uri=FIXED_CALLBACK_URL
            )
        return OAuth2Session(
            CLIENT_ID,
            redirect_uri=FIXED_CALLBACK_URL,
        )

    @staticmethod
    def logout():

        # Clear session stored data
        flask.session.clear()

        # Redirect user to logout endpoint
        return_url = flask.request.host_url
        params = {'returnTo': return_url, 'client_id': CLIENT_ID}
        r = flask.redirect(LOGOUT_URL + '?' + urlencode(params))
        r.delete_cookie(COOKIE_AUTH_USER_NAME)
        r.delete_cookie(COOKIE_AUTH_ACCESS_TOKEN)

        return r