from django.contrib import admin

# Register your models here.
from appcivist.models import Assembly

class AssemblyAdmin(admin.ModelAdmin):
	list_display = ('appcivist_id', 'name', 'url')
	ordering = ('appcivist_id', 'name', 'url')

admin.site.register(Assembly, AssemblyAdmin)