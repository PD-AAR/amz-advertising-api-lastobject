import requests
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

IAM_SCOPE = "https://www.googleapis.com/auth/iam"
OAUTH_TOKEN_URI = "https://www.googleapis.com/oauth2/v4/token"
DEFAULT_TIME_OUT = 540  # 9 minutes


def requests_retry_session(
    retries: int = 3,
    backoff_factor: float = 1,
    status_forcelist: tuple = (500, 502, 503, 504),
    method_whitelist: list = None,
    session: requests.Session = None,
) -> requests.Session:
    """
    Creates a requests.Session object for making HTTP calls with a Retry set
    :param retries: number of times to retry on failure
    :param backoff_factor: A backoff factor to apply between attempts after the second try, docs below
        https://urllib3.readthedocs.io/en/latest/reference/urllib3.util.html#module-urllib3.util.retry
    :param status_forcelist: tuple of http status to trigger a retry
    :param method_whitelist: list of HTTP methods to include in retry trigger
    :param session: requests.session object, default to none and creates one
    :return: requests.Session object with Retry mounted
    """
    session = session or requests.Session()
    method_whitelist = method_whitelist or Retry.DEFAULT_METHOD_WHITELIST
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        method_whitelist=method_whitelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def make_iap_request(url, client_id, method="GET", **kwargs):
    """Makes a request to an application protected by Identity-Aware Proxy.

    Args:
      url: The Identity-Aware Proxy-protected URL to fetch.
      client_id: The client ID used by Identity-Aware Proxy.
      method: The request method to use
              ('GET', 'OPTIONS', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE')
      **kwargs: Any of the parameters defined for the request function:
                https://github.com/requests/requests/blob/master/requests/api.py
                If no timeout is provided, it is set to 90 by default.

    Returns:
      The page body, or raises an exception if the page couldn't be retrieved.
    """
    # Set the default timeout, if missing
    if "timeout" not in kwargs:
        kwargs["timeout"] = 90

    # Obtain an OpenID Connect (OIDC) token from metadata server or using service
    # account.
    open_id_connect_token = id_token.fetch_id_token(Request(), client_id)

    # Fetch the Identity-Aware Proxy-protected URL, including an
    # Authorization header containing "Bearer " followed by a
    # Google-issued OpenID Connect token for the service account.
    sess = requests_retry_session()
    resp = sess.request(method, url, headers={"Authorization": "Bearer {}".format(open_id_connect_token)}, **kwargs)
    if resp.status_code == 403:
        raise Exception("Service account does not have permission to " "access the IAP-protected application.")
    elif resp.status_code != 200:
        raise Exception(
            "Bad response from application: {!r} / {!r} / {!r}".format(resp.status_code, resp.headers, resp.text)
        )
    else:
        return resp
