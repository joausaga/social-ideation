import requests

from django.http import HttpResponseServerError, HttpResponse
from .models import Connector
from .error import ConnectorError


def test_connector(request, connector_id):
    connector = Connector.objects.get(id=connector_id)
    url_callbacks = connector.url_callback.all()
    comment_to_delete_id, idea_to_delete_id, user_to_delete_id = None, None, None
    try:
        testing_params = _get_testing_param(url_callbacks)
        for url_cb in url_callbacks:
            callback = url_cb.callback
            if callback.name != 'testing_param_cb':
                url = url_cb.url
                cb_params = callback.params.all()
                req_param = {}
                for cb_param in cb_params:
                    req_param[cb_param.name] = testing_params[cb_param.name]
                if callback.method == 'POST':
                    resp = requests.post(url, data=req_param)
                    ret_obj = resp.json()
                    if callback.name == 'create_idea_cb':
                        idea_to_delete_id = ret_obj['id']
                    if callback.name == 'create_user_cb':
                        user_to_delete_id = ret_obj['id']
                    if callback.name == 'create_comment_idea':
                        comment_to_delete_id = ret_obj['id']
                elif callback.method == 'DELETE':
                    if callback.name == 'delete_comment_cb':
                        req_param['comment_id'] = comment_to_delete_id
                    if callback.name == 'delete_idea_cb':
                        req_param['idea_id'] = idea_to_delete_id
                    if callback.name == 'delete_idea_cb':
                        req_param['user_id'] = user_to_delete_id
                    resp = requests.delete(url, data=req_param)
                    ret_obj = resp.json()
                else:
                    resp = requests.get(url, params=req_param)
                    ret_obj = resp.json()
                _check_cb_return_obj(callback, ret_obj)
        HttpResponse("The connect is ok and ready to be used")
    except ConnectorError as e:
        HttpResponseServerError('Error in connector\'s callbacks. Reason: {}'.format(e.reason))


def _testing_param_cb(url_callbacks):
    for url_cb in url_callbacks:
        if url_cb.callback.name == 'testing_param_cb':
            return url_cb


def _get_testing_param(url_callbacks):
    testing_cb = _testing_param_cb(url_callbacks)
    resp = requests.get(testing_cb.url)
    ret_obj = resp.json()
    _check_cb_return_obj(testing_cb, ret_obj)
    return ret_obj


def _check_cb_return_obj(callback, ret_obj):
    expected_ret_obj = callback.return_object

    if callback.return_type == 'set':
        for obj in ret_obj:
            _check_simple_attrs(obj, ret_obj)
            _check_composed_attrs(obj, ret_obj)
    else:
        _check_simple_attrs(expected_ret_obj, ret_obj)
        _check_composed_attrs(expected_ret_obj, ret_obj)

    return True


def _check_simple_attrs(expected_ret_obj, ret_obj):
    for attr in expected_ret_obj.attributes.all():
        if attr.name not in ret_obj.keys():
            if attr.required:
                raise ConnectorError('Required attribute {} not received'.format(attr.name))
        else:
            value = ret_obj[attr.name]
            _check_type_attr(attr.name, attr.type, value)


def _check_composed_attrs(expected_ret_obj, ret_obj):
    for composed_attr in expected_ret_obj.composed_attributes.all():
        if composed_attr.name not in ret_obj.keys():
            raise ConnectorError('Required attribute {} not received'.format(composed_attr.name))
        _check_simple_attrs(composed_attr, ret_obj[composed_attr.name])


def _check_type_attr(attr_name, attr_type, value):
    if attr_type == 'str' and not type(value).__name__ == 'str':
        raise ConnectorError('Attribute {} type mismatch, expected string received {}'.format(attr_name, type(value)))
    elif attr_type == 'num' and not type(value).__name__ == 'int':
        raise ConnectorError('Attribute {} type mismatch, expected string received {}'.format(attr_name, type(value)))
    else:
        if not type(value).__name__ == 'bool':
            raise ConnectorError('Attribute {} type mismatch, expected string received {}'.format(attr_name, type(value)))
