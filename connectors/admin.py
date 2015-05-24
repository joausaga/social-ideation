import requests

from django import forms
from django.contrib import admin, messages
from django.utils.html import format_html

from connectors.models import Parameter, Object, Callback, MetaConnector, Connector, BasicAttribute, ComposedAttribute, \
                              URLCallback, URLParameter, SocialNetworkConnector
from connectors.error import ConnectorError


def get_type_name(type):
    if type == 'bool':
        return 'boolean'
    elif type == 'num':
        return 'number'
    elif type == 'str':
        return 'string'
    else:
        return type


class ObjectForm(forms.ModelForm):

    class Meta:
        model = Object
        fields = '__all__'

    def clean(self):
        # TODO: Check if the object is being created without attributes
        pass


class ObjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'print_object_attributes')
    ordering = ('name',)
    filter_horizontal = ('attributes', 'composed_attributes',)
    form = ObjectForm

    def print_object_attributes(self, obj):
        str_attr = ''
        attrs = obj.object_attributes()
        attr_counter = 1
        for attr in attrs:
            if attr['type'] == 'composed':
                str_attr += "<b>"
            if not attr['required']:
                str_attr += attr['name'] + "</b> (" + get_type_name(attr['type_name']) + ")"
            else:
                str_attr += attr['name'] + "</b> (" + get_type_name(attr['type_name']) + " - <i>required</i>)"
            if attr_counter != len(attrs):
                str_attr += '<br>'
            attr_counter += 1
        return format_html(str_attr)
    print_object_attributes.short_description = 'Attributes'


class CallbackAdmin(admin.ModelAdmin):
    list_display = ('name', 'method', 'print_body_parameters', 'print_url_parameters','required', 'print_return_object',
                    'return_format')
    ordering = ('name', 'method',)
    filter_horizontal = ('body_params', 'url_params')

    def print_parameters(self, params):
        str_params = ''
        param_counter = 1
        for param in params:
            if not param['required']:
                str_params += param['name'] + " (" + get_type_name(param['type']) + ")"
            else:
                str_params += param['name'] + " (" + get_type_name(param['type']) + " - <i>required</i>)"
            if param_counter != len(params):
                str_params += '<br>'
            param_counter += 1
        return str_params

    def print_body_parameters(self, obj):
        return format_html(self.print_parameters(obj.parameters('body_params')))
    print_body_parameters.short_description = 'Body Parameters'

    def return_format(self, obj):
        return obj.format

    def print_url_parameters(self, obj):
        return format_html(self.print_parameters(obj.parameters('url_params')))
    print_url_parameters.short_description = 'URL Parameters'

    def print_return_object(self, obj):
        if obj.return_type == 'set':
            str_ret_obj = '<b><i> Array of ' + obj.return_object.name + 's</i></b>, where each ' + \
                          obj.return_object.name.lower() + ' is composed of <br>'
        else:
            str_ret_obj = '<b><i>' + obj.return_object.name + '</i></b> composed of<br>'
        ret_obj_attrs = obj.return_object.object_attributes()
        attr_counter = 1
        for attr in ret_obj_attrs:
            if attr['type'] == 'composed':
                str_ret_obj += "<b>"
            if not attr['required']:
                str_ret_obj += '- ' + attr['name'] + "</b> (" + get_type_name(attr['type_name']) + ")"
            else:
                str_ret_obj += '- ' + attr['name'] + "</b> (" + get_type_name(attr['type_name']) + " - <i>required</i>)"
            if attr_counter != len(ret_obj_attrs):
                str_ret_obj += '<br>'
            attr_counter += 1
        return format_html(str_ret_obj)
    print_return_object.short_description = 'Return Object'


class ParameterAdmin(admin.ModelAdmin):
    list_display = ('name', 'print_type', 'required')
    ordering = ('name', 'type',)

    def print_type(self, obj):
        return get_type_name(obj.type)
    print_type.short_description = 'Type'


class URLParameterAdmin(admin.ModelAdmin):
    list_display = ('name', 'print_type', 'required')
    ordering = ('name', 'type',)

    def print_type(self, obj):
        return get_type_name(obj.type)
    print_type.short_description = 'Type'


class AttributeAdmin(admin.ModelAdmin):
    list_display = ('name', 'print_type', 'required', 'empty')
    ordering = ('name', 'type',)

    def print_type(self, obj):
        return get_type_name(obj.type)
    print_type.short_description = 'Type'


class ComposedAttributeAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'required', 'empty')
    ordering = ('name', 'type',)


class MetaConnectorAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'print_callbacks')
    ordering = ('name', 'type',)
    filter_horizontal = ('callbacks',)

    def print_callbacks(self, obj):
        str_callbacks = ''
        callback_counter = 1
        callbacks = obj.callbacks.all()
        for callback in callbacks:
            if not callback.required:
                str_callbacks += callback.name + ' <b><i>(optional)</i></b>'
            else:
                str_callbacks += callback.name
            if callback_counter != len(callbacks):
                str_callbacks += '<br>'
            callback_counter += 1
        return format_html(str_callbacks)
    print_callbacks.short_description = 'Callbacks'


class URLCallbackAdmin(admin.ModelAdmin):
    fields = ['callback', 'url']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'callback' and 'mcid' in request.GET.keys():
            mc_im = MetaConnector.objects.get(id=request.GET['mcid'])
            kwargs['queryset'] = Callback.objects.filter(metaconnector=mc_im)
        return super(URLCallbackAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        obj.status = 'untested'
        obj.save(form=form)


class ConnectorForm(forms.ModelForm):

    class Meta:
        model = Connector
        fields = '__all__'

    def clean(self):
        # TODO: Check if all the callbacks associated to the selected meta connector have a corresponding url
        # TODO: Check if all url associated to callbacks work as expected
        pass


class ConnectorAdmin(admin.ModelAdmin):
    list_display = ('name', 'meta_connector', 'print_callbacks')
    ordering = ('name', 'meta_connector',)
    form = ConnectorForm
    actions = ['test_connector_callbacks']
    filter_horizontal = ('url_callback',)

    class Media:
        from django.conf import settings
        static_url = getattr(settings, 'STATIC', '/static')
        js = [ static_url+'/js/modify_url.js', ]

    def print_callbacks(self, obj):
        str_callbacks = ''
        url_callbacks = obj.url_callback.all()
        str_callbacks += '<table>'
        str_callbacks += '<tr align="center"><td align="center"><b>Name</b></td><td><b>URI</b></td>' \
                         '<td align="center"><b>Status</b></td></tr>'
        for url_callback in url_callbacks:
            str_callbacks += '<tr>'
            str_callbacks += '<td>'+ url_callback.callback.name + '</td>'
            str_callbacks += '<td>' + url_callback.url + '</td>'
            if url_callback.status == 'ok':
                str_callbacks += '<td align="center"><b><font color="green">OK</font></b></td>'
            elif url_callback.status == 'failure':
                str_callbacks += '<td align="center"><b><font color="red">Failure</font></b></td>'
            else:
                str_callbacks += '<td align="center">Untested</td>'
            str_callbacks += '</tr>'
        str_callbacks += '</table>'
        return format_html(str_callbacks)
    print_callbacks.short_description = 'Callbacks'

    def test_connector_callbacks(self, request, queryset):
        try:
            for obj in queryset:
                test_connector(obj)
            self.message_user(request, 'The callbacks of the selected connector(s) are working and ready to be used')
        except ConnectorError as e:
            self.message_user(request, e.reason, level=messages.ERROR)
    test_connector_callbacks.short_description = "Test Connector Callbacks"

# ---
# Functions to test connector callbacks
# ---


def test_connector(connector):
    _check_connector_status(connector)
    url_callbacks = _order_url_callbacks(connector.url_callback.exclude(status='ok'), 'testing')
    comment_to_delete_id, idea_to_delete_id, user_to_delete_id = None, None, None
    testing_params = _get_testing_param(connector)
    for url_cb in url_callbacks:
        callback = url_cb.callback
        if callback.name != 'testing_param_cb':
            print('Callback: %s' % callback.name)
            req_param = _build_request_body(connector, callback, testing_params)
            if callback.method.upper() == 'POST':
                url = build_request_url(url_cb.url, callback, testing_params)
                resp = do_request(connector, url, callback.method, req_param)
            elif callback.method.upper() == 'DELETE':
                del_params = {'comment_id': comment_to_delete_id, 'idea_id': idea_to_delete_id, 'user_id': user_to_delete_id}
                url = build_request_url(url_cb.url, callback, del_params)
                resp = do_request(connector, url, callback.method, req_param)
            else:
                url = build_request_url(url_cb.url, callback, testing_params)
                resp = do_request(connector, url, callback.method)
            try:
                ret_obj = get_json_or_error(connector.name, callback, resp)
                _check_cb_return_obj(connector.name, callback, ret_obj)
                if callback.method.upper() == 'POST' and callback.name.find('create') != -1:
                    if callback.name.find('comment') != -1:
                        comment_to_delete_id = ret_obj['id']
                    elif callback.name.find('idea') != -1:
                        idea_to_delete_id = ret_obj['id']
                    elif callback.name.find('user') != -1:
                        user_to_delete_id = ret_obj['id']
                url_cb.status = 'ok'
                url_cb.save()
            except Exception, e:
                url_cb.status = 'failure'
                url_cb.save()
                raise e


def _check_connector_status(connector):
    del_failure = False
    for url_cb in _order_url_callbacks(connector.url_callback.all()):
        callback = url_cb.callback
        if callback.method.upper() == 'GET':
            continue
        elif callback.method.upper() == 'DELETE':
            if url_cb.status == 'failure':
                del_failure = True
        elif callback.method.upper() == 'POST':
            if del_failure:
                # Delete callbacks depend on create callbacks. Therefore, if a delete callback is found
                # in failure status then the status of all create callbacks (post) will be set to 'untested'
                url_cb.status = 'untested'
                url_cb.save()


def _order_url_callbacks(url_callbacks, order_criteria='alpha'):
    get_url_cb, post_url_cb, del_url_cb = [], [], []
    for url_cb in url_callbacks:
        if url_cb.callback.method.upper() == 'GET':
            get_url_cb.append(url_cb)
        elif url_cb.callback.method.upper() == 'POST':
            post_url_cb.append(url_cb)
        else:
            del_url_cb.append(url_cb)
    if order_criteria == 'alpha':
        return get_url_cb + del_url_cb + post_url_cb
    else:
        return get_url_cb + post_url_cb + del_url_cb


def build_request_url(url, callback, url_params):
    cb_url_params = callback.url_params.all()
    for cb_url_param in cb_url_params:
        url = url.replace('{}'.format(cb_url_param.name), str(url_params[cb_url_param.name]))
    return url


def _build_request_body(connector, callback, testing_params):
    req_param = {}
    cb_body_params = callback.body_params.all()
    for cb_body_param in cb_body_params:
        try:
            req_param[cb_body_param.name] = testing_params[cb_body_param.name]
        except KeyError:
            if cb_body_param.required:
                raise ConnectorError('Parameter {} missing. It required for calling {}, which is a callback of '
                                     'the connector {}. The callback testing_param_cb must include this '
                                     'parameter as part of the parameter set'
                                     .format(cb_body_param.name, callback.name, connector.name))
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
            return response.txt()
        else:
            raise ConnectorError('Error, do not understand response of callback {} of the connector {}. Expected '
                                 'json or xml'.format(cb.name, connector_name))


def get_url_cb(connector, name):
    for url_cb in connector.url_callback.all():
        if url_cb.callback.name == name:
            return url_cb
    raise ConnectorError('The callback \'{}\' needed to obtain testing parameters was not defined'.format(name))


def _get_testing_param(connector):
    testing_url_cb = get_url_cb(connector, 'get_testing_param_cb')
    resp = do_request(connector, testing_url_cb.url, testing_url_cb.callback.method)
    ret_obj = get_json_or_error(connector.name, testing_url_cb.callback, resp)
    _check_cb_return_obj(connector.name, testing_url_cb.callback, ret_obj)
    return ret_obj


def _check_cb_return_obj(connector_name, callback, ret_obj):
    expected_ret_obj = callback.return_object

    if len(ret_obj) > 0:
        if callback.return_type == 'set':
            for obj in ret_obj:
                _check_simple_attrs(connector_name, callback.name, expected_ret_obj, obj)
                _check_composed_attrs(connector_name, callback.name, expected_ret_obj, obj)
        else:
            _check_simple_attrs(connector_name, callback.name, expected_ret_obj, ret_obj)
            _check_composed_attrs(connector_name, callback.name, expected_ret_obj, ret_obj)
        return True
    else:
       raise ConnectorError('Received an empty response. Connector: {}, callback: {}'.
                             format(connector_name, callback.name))


def _check_simple_attrs(connector_name, cb_name, expected_ret_obj, ret_obj):
    for attr in expected_ret_obj.attributes.all():
        if attr.name not in ret_obj.keys():
            if attr.required:
                raise ConnectorError('Required attribute "{}" not received. Connector: {}, callback: {}'.
                                     format(attr.name, connector_name, cb_name))
        else:
            value = ret_obj[attr.name]
            _check_type_attr(connector_name, cb_name, attr, value)


def _check_composed_attrs(connector_name, cb_name, expected_ret_obj, ret_obj):
    for composed_attr in expected_ret_obj.composed_attributes.all():
        if composed_attr.name not in ret_obj.keys():
            raise ConnectorError('Required attribute "{}" not received. Connector: {}, callback: {}'.
                                 format(composed_attr.name, cb_name, connector_name))
        _check_simple_attrs(connector_name, cb_name, composed_attr.type, ret_obj[composed_attr.name])


def _check_type_attr(connector_name, cb_name, attr, value):
    if type(value) == type(None):
        if attr.empty:
            return
        else:
            raise ConnectorError('Attribute "{}" cannot be empty. Connector: {}, callback: {}'
                                 .format(attr.name, connector_name, cb_name))
    else:
        if attr.type == 'str':
            if not isinstance(value, (basestring)):
                raise ConnectorError('Attribute "{}" type mismatch, expected string received {}. Connector: {}, callback: {}'
                                     .format(attr.name, type(value).__name__, connector_name, cb_name))
        elif attr.type == 'num':
            if not isinstance(value, (int, long, float)):
                raise ConnectorError('Attribute "{}" type mismatch, expected string received {}. Connector: {}, callback: {}'
                                     .format(attr.name, type(value).__name__, connector_name, cb_name))
        else:
            if not isinstance(value, bool):
                raise ConnectorError('Attribute "{}" type mismatch, expected string received {}. Connector: {}, callback: {}'
                                     .format(attr.name, type(value).__name__, connector_name, cb_name))


# ---
#
# ---

admin.site.register(Parameter, ParameterAdmin)

admin.site.register(URLParameter, URLParameterAdmin)

admin.site.register(BasicAttribute, AttributeAdmin)

admin.site.register(Object, ObjectAdmin)

admin.site.register(Callback, CallbackAdmin)

admin.site.register(MetaConnector, MetaConnectorAdmin)

admin.site.register(Connector, ConnectorAdmin)

admin.site.register(URLCallback, URLCallbackAdmin)

admin.site.register(ComposedAttribute, ComposedAttributeAdmin)

admin.site.register(SocialNetworkConnector)