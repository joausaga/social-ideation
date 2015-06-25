from django.db import models

# imported = getattr(__import__(my_module, fromlist=[my_class]), my_class)


BASIC_TYPES = (
    ('str', 'String'),
    ('num', 'Number'),
    ('bool', 'Boolean'),
)


class SocialNetworkConnector(models.Model):
    name = models.CharField(max_length=50)
    connector_module = models.CharField(max_length=50)
    connector_class = models.CharField(max_length=50)
    active = models.BooleanField(null=False, default=False)

    def __unicode__(self):
        return self.name


class Parameter(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=150, null=True, blank=True)
    type = models.CharField(max_length=50, choices=BASIC_TYPES)
    required = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name


class URLParameter(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=150, null=True, blank=True)
    type = models.CharField(max_length=50, choices=BASIC_TYPES)
    required = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name


class BasicAttribute(models.Model):
    name = models.CharField(max_length=50)
    type = models.CharField(max_length=50, choices=BASIC_TYPES)
    required = models.BooleanField(default=True)
    empty = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name


class ComposedAttribute(models.Model):
    name = models.CharField(max_length=50)
    type = models.ForeignKey('Object')
    required = models.BooleanField(default=True)
    empty = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name


class Object(models.Model):
    name = models.CharField(max_length=50)
    attributes = models.ManyToManyField(BasicAttribute, blank=True)
    composed_attributes = models.ManyToManyField(ComposedAttribute, blank=True)

    def __unicode__(self):
        return self.name

    def object_attributes(self):
        attrs = []
        # Simple Attributes
        for attr in self.attributes.all():
            attr_dict = {
                'name': attr.name,
                'type': 'simple',
                'type_name': attr.type,
                'required': attr.required
            }
            attrs.append(attr_dict)
        # Composed Attributes
        for attr in self.composed_attributes.all():
            attr_dict = {
                'name': attr.name,
                'type': 'composed',
                'type_name': attr.type.name,
                'required': attr.required
            }
            attrs.append(attr_dict)
        return attrs


class Callback(models.Model):
    name = models.CharField(max_length=50)
    METHOD = (
        ('get', 'GET'),
        ('post', 'POST'),
        ('delete', 'DELETE'),
    )
    FORMAT = (
        ('json', 'JSON'),
        ('xml', 'XML'),
        ('txt', 'TXT'),
    )
    RETURN_TYPES = (
        ('set', 'Set'),
        ('unit', 'Unit'),
    )
    return_type = models.CharField(max_length=50, choices=RETURN_TYPES, default='set')
    return_object = models.ForeignKey(Object)
    method = models.CharField(max_length=50, choices=METHOD)
    format = models.CharField(max_length=50, choices=FORMAT)
    required = models.BooleanField(default=True)
    body_params = models.ManyToManyField(Parameter, blank=True)
    url_params = models.ManyToManyField(URLParameter, blank=True)

    def __unicode__(self):
        if not self.required:
            return self.name + ' (optional)'
        else:
            return self.name

    def parameters(self, type):
        params = []
        for param in getattr(self, type).all():
            param_dict = {
                'name': param.name,
                'type': param.type,
                'required': param.required
            }
            params.append(param_dict)

        return params


class MetaConnector(models.Model):
    name = models.CharField(max_length=50)
    TYPES = (
        ('social_network', 'Social Network'),
        ('idea_mgmt', 'Idea Management'),
    )
    type = models.CharField(max_length=50, choices=TYPES)
    callbacks = models.ManyToManyField(Callback)

    def __unicode__(self):
        return self.name


class Connector(models.Model):
    name = models.CharField(max_length=50)
    authentication = models.BooleanField(default=False)
    auth_header = models.CharField(max_length=50, null=True, blank=True)
    auth_token = models.CharField(max_length=255, null=True, blank=True)
    meta_connector = models.ForeignKey(MetaConnector)
    url_callback = models.ManyToManyField('URLCallback')

    def __unicode__(self):
        return self.name


class URLCallback(models.Model):
    callback = models.ForeignKey(Callback)
    url = models.URLField(null=True)
    STATUSES = (
        ('ok', 'Ok'),
        ('untested', 'Untested'),
        ('failure', 'Failure'),
    )
    status = models.CharField(max_length=50, choices=STATUSES, default='untested')

    def __unicode__(self):
        return self.callback.name + ': ' + self.url
