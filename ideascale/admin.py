from django.contrib import admin

from .models import Initiative, TestingParameters


class InitiativeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'url')
    ordering = ('id', 'name', 'url')

class TestingParamAdmin(admin.ModelAdmin):
    list_display = ('key', 'raw_value', 'type')
    ordering = ('key', 'raw_value', 'type')

admin.site.register(Initiative, InitiativeAdmin)
admin.site.register(TestingParameters, TestingParamAdmin)
