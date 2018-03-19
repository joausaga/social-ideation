from django.contrib import admin

# Register your models here.
from appcivist.models import Campaign

class CampaignAdmin(admin.ModelAdmin):
	list_display = ('appcivist_id', 'assembly_id', 'name', 'url')
	ordering = ('appcivist_id', 'assembly_id', 'name', 'url')

admin.site.register(Campaign, CampaignAdmin)
