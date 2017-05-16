import datetime
import requests
import re
import unicodedata
import six

from django.utils import timezone
from django.utils.encoding import smart_str, smart_unicode
from celery.utils.log import get_task_logger
from connectors.error import ConnectorError


logger = get_task_logger(__name__)


def build_request_url(url, callback, url_params):
    cb_url_params = callback.url_params.all()
    for cb_url_param in cb_url_params:
        url = url.replace('{}'.format(cb_url_param.name), str(url_params[cb_url_param.name]))
    return url


def build_request_body(connector, callback, params):
    req_param = {}
    cb_body_params = callback.body_params.all()
    for cb_body_param in cb_body_params:
        try:
            req_param[cb_body_param.name] = params[cb_body_param.name]
        except KeyError:
            if cb_body_param.required:
                raise ConnectorError('Parameter {} missing. It required for calling {}, which is a callback of '
                                     'the connector {}. The callback must include this parameter as part of the '
                                     'parameter set'.format(cb_body_param.name, callback.name, connector.name))
    return req_param


def do_request(connector, url, method, params=None):
    auth_header = None
    if connector.authentication:
        auth_header = {connector.auth_header: connector.auth_token}
    request_params = {'url': url}
    if auth_header and params:
        request_params.update({'headers': auth_header, 'data': params})
    else:
        if auth_header:
            request_params.update({'headers': auth_header})
        else:
            request_params.update({'data': params})
    if method.upper() == 'POST':
        return requests.post(**request_params)
    elif method.upper() == 'DELETE':
        return requests.delete(**request_params)
    else:
        return requests.get(**request_params)


def get_json_or_error(connector_name, cb, response):
    if response.status_code and not 200 <= response.status_code < 300:
        raise ConnectorError('Error when calling the callback {} of the connector {}. Message: {}'
                             .format(cb.name, connector_name, response.content))
    else:
        if cb.format == 'json':
            return response.json()
        elif cb.format == 'xml':
            return response.xml()
        elif cb.format == 'txt':
            return response.text
        else:
            raise ConnectorError('Error, do not understand response of callback {} of the connector {}. Expected '
                                 'json or xml'.format(cb.name, connector_name))


def get_url_cb(connector, name):
    for url_cb in connector.url_callback.all():
        if url_cb.callback.name == name:
            return url_cb
    raise ConnectorError('The callback \'{}\' was not defined in the connector {}'.format(name, connector))


def generate_email_address(name):
    name = name.lower().replace(' ','').strip()
    validated_name = validate_email_local_part(name)
    return validated_name + '@social-ideation.org'


# Validate whether 'str' is a valid string for the local part of an email address
# Written by JoshData (https://github.com/JoshData/python-email-validator)
def validate_email_local_part(str):
    # Based on RFC 2822 section 3.2.4 / RFC 5322 section 3.2.3, these
    # characters are permitted in email addresses (not taking into
    # account internationalization):
    ATEXT = r'a-zA-Z0-9_!#\$%&\'\*\+\-/=\?\^`\{\|\}~'

    # A "dot atom text", per RFC 2822 3.2.4:
    DOT_ATOM_TEXT = '[' + ATEXT + ']+(?:\\.[' + ATEXT + ']+)*'

    # RFC 6531 section 3.3 extends the allowed characters in internationalized
    # addresses to also include three specific ranges of UTF8 defined in
    # RFC3629 section 4, which appear to be the Unicode code points from
    # U+0080 to U+10FFFF.
    ATEXT_UTF8 = ATEXT + u"\u0080-\U0010FFFF"
    DOT_ATOM_TEXT_UTF8 = '[' + ATEXT_UTF8 + ']+(?:\\.[' + ATEXT_UTF8 + ']+)*'

    if len(str) == 0:
        raise Exception('The email local part cannot be empty.')

    # RFC 5321 4.5.3.1.1
    if len(str) > 64:
        return str[0:63]

    # Check the local part against the regular expression for the older ASCII requirements.
    m = re.match(DOT_ATOM_TEXT + "$", str)
    if m:
        # Return str unchanged
        return str

    else:
        # The local part failed the ASCII check. Remove bad characters
        m = re.match(DOT_ATOM_TEXT_UTF8 + '$', str)
        if not m:
            local = ''
            for c in str:
                if re.match(u"[" + ATEXT + u"]", c):
                    local += c
        else:
            local = str

        # RFC 6532 section 3.1 also says that Unicode NFC normalization should be applied,
        # so we'll return the normalized local part in the return value.
        local = unicodedata.normalize("NFC", local)

        return local


def convert_to_utf8_str(arg):
    try:
        return smart_str(arg)
    except:
        # written by Michael Norton (http://docondev.blogspot.com/)
        if isinstance(arg, six.text_type):
            arg = arg.encode('utf-8')
        elif not isinstance(arg, bytes):
            arg = six.text_type(arg).encode('utf-8')
        elif isinstance(arg, bytes):
            arg = arg.decode('utf-8')
        return arg
        #return str(arg)


def get_timezone_aware_datetime(datetime):
    return timezone.make_aware(datetime, timezone.get_default_timezone())


def calculate_token_expiration_time(secs):
    str_secs = convert_to_utf8_str(secs)
    int_secs = int(str_secs)
    return datetime.datetime.now() + datetime.timedelta(seconds=int_secs)


def call_social_network_api(connector, method, params=None, error_handler_method=None):
    sn_class = connector.connector_class.title()
    sn_module = connector.connector_module.lower()
    sn = getattr(__import__(sn_module, fromlist=[sn_class]), sn_class)
    try:
        if params:
            return getattr(sn, method)(**params)
        else:
            return getattr(sn, method)()
    except Exception as e:
        if not error_handler_method:
            getattr(sn, 'error_handler')(method, e, params)
        else:
            getattr(sn, error_handler_method)(method, e, params)
