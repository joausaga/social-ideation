from django.contrib import admin, messages
from app.models import ConsultationPlatform, Initiative, Campaign, SocialNetwork, Idea, Comment, Vote
from app.tasks import synchronize_content, test_function
from connectors.admin import do_request, get_json_or_error, get_url_cb, build_request_url
from connectors.error import ConnectorError


class SocialNetworkAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'connector', )
    ordering = ('name', 'url', )


class InitiativeAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'consultation_platform', 'social_networks', 'hashtag', 'users', 'ideas', 'votes', 'comments', 'active', )
    ordering = ('name', 'url', 'hashtag', 'users', 'ideas', 'votes', 'comments', 'active', )

    def consultation_platform(self, obj):
        return obj.platform
    consultation_platform.short_description = 'Consultation Platform'

    def has_add_permission(self, request):
        return False

    def social_networks(self, obj):
        str_sn = ''
        num_sns = len(obj.social_network.all())
        idx_sn = 1
        for social_net in obj.social_network.all():
            str_sn += str_sn + social_net.name
            if idx_sn < num_sns:
                 str_sn += ', '
            idx_sn += 1
        if str_sn == '': str_sn = 'None'
        return str_sn
    social_networks.short_description = 'Social Networks'


class CampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'initiative', 'hashtag', )
    ordering = ('name', 'initiative', 'hashtag', )

    def has_add_permission(self, request):
        return False


class ConsultationPlatformAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'connector')
    ordering = ('name', 'url',)
    actions = ['get_platform_initiative']

    def _cu_campaigns(self, platform, ini_obj):
        connector = platform.connector
        campaigns_url_cb = get_url_cb(connector, 'get_campaigns_cb')
        url = build_request_url(campaigns_url_cb .url, campaigns_url_cb .callback, {'initiative_id': ini_obj.external_id})
        resp = do_request(connector, url, campaigns_url_cb.callback.method)
        campaigns = get_json_or_error(connector.name, campaigns_url_cb.callback, resp)
        if len(campaigns) > 0:
            for campaign in campaigns:
                cam_obj, created = Campaign.objects.get_or_create(external_id=campaign['id'], initiative=ini_obj,
                                                                  defaults={'name': campaign['name']})
                name_formatted = campaign['name'].replace(" ", "").lower()
                if created:
                    if len(name_formatted) > 14:
                        name_formatted = name_formatted[0:14]
                    cam_obj.hashtag = name_formatted
                    cam_obj.save()
        else:
            camp_objs = Campaign.object.filter(initiative=ini_obj)
            if len(camp_objs) == 0:
                default_campaign = Campaign(external_id=-1, initiative=ini_obj, name='default')
                default_campaign.save()

    def _cu_initiatives(self, platform, initiatives):
        new_initiatives = 0
        for initiative in initiatives:
            ini_obj, created = Initiative.objects.get_or_create(external_id=initiative['id'], platform=platform,
                                                                url=initiative['url'], defaults={'name': initiative['name']})
            name_formatted = initiative['name'].replace(" ", "").lower()
            if created:
                new_initiatives += 1
                if len(name_formatted) > 14:
                    name_formatted = name_formatted[0:14]
                ini_obj.hashtag = name_formatted
                ini_obj.save()
            self._cu_campaigns(platform, ini_obj)
        return new_initiatives

    def get_platform_initiative(self, request, queryset):
        try:
            new_initiatives = 0
            for platform in queryset:
                connector = platform.connector
                initiatives_url_cb = get_url_cb(connector, 'get_initiatives_cb')
                resp = do_request(connector, initiatives_url_cb.url, initiatives_url_cb.callback.method)
                ret_obj = get_json_or_error(connector.name, initiatives_url_cb.callback, resp)
                new_initiatives = self._cu_initiatives(platform, ret_obj)
            if new_initiatives == 0:
                self.message_user(request, 'None new initiative was found in the selected platform(s).')
            elif new_initiatives == 1:
                self.message_user(request, 'A new initiative was obtained from the selected platform(s) and stored in '
                                           'the system. Don\'t forget to activate it if you want it to be '
                                           'synchronized.')
            else:
                self.message_user(request, '{} new initiatives were obtained from the selected platform(s) and stored in '
                                           'the system. Don\'t forget to activate them if you want them to be '
                                           'synchronized.'.format(new_initiatives))
        except ConnectorError as e:
            self.message_user(request, e.reason, level=messages.ERROR)
        except Exception as e:
            self.message_user(request, e, level=messages.ERROR)
    get_platform_initiative.short_description = "Get Initiatives"

    # Temporal to test how the implementation works
    def sync_content(self, request, queryset):
        test_function()
        #synchronize_content()
    sync_content.short_description = "Synchronize Content"


class IdeaAdmin(admin.ModelAdmin):
    list_display = ('idea_id', 'idea_source', 'initiative', 'campaign', 'author', 'datetime', 'title', 'text',
                    're_posts', 'bookmarks', 'positive_votes', 'negative_votes', 'comments', 'sync', 'has_changed')
    ordering = ('initiative', 'campaign', 'author', 'datetime', 'positive_votes', 'negative_votes', 'comments')
    list_filter = ['initiative']

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        qs = super(IdeaAdmin, self).get_queryset(request)
        return qs.filter(exist=True)

    def idea_id(self, obj):
        if obj.source == 'consultation_platform':
            return obj.cp_id
        else:
            return obj.sn_id
    idea_id.short_description = 'Id'

    def idea_source(self, obj):
        if obj.source_consultation:
            return obj.source_consultation.name.title()
        else:
            return obj.source_social.name.title()
    idea_source.short_description = 'Source'


class CommentAdmin(admin.ModelAdmin):
    list_display = ('comment_id', 'comment_source', 'initiative', 'campaign', 'author', 'datetime', 'text', 'parent',
                    'positive_votes', 'negative_votes', 'comments', 'sync')
    ordering = ('initiative', 'campaign', 'author', 'datetime', 'positive_votes', 'negative_votes', 'comments')
    list_filter = ['initiative']

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        qs = super(CommentAdmin, self).get_queryset(request)
        return qs.filter(exist=True)

    def comment_id(self, obj):
        if obj.source == 'consultation_platform':
            return obj.cp_id
        else:
            return obj.sn_id
    comment_id.short_description = 'Id'

    def comment_source(self, obj):
        if obj.source_consultation:
            return obj.source_consultation.name.title()
        else:
            return obj.source_social.name.title()
    comment_source.short_description = 'Source'


class VoteAdmin(admin.ModelAdmin):
    list_display = ('vote_id', 'vote_source', 'initiative', 'campaign', 'author', 'datetime', 'value', 'parent', 'sync')
    ordering = ('initiative', 'campaign', 'author')
    list_filter = ['initiative']

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        qs = super(VoteAdmin, self).get_queryset(request)
        return qs.filter(exist=True)

    def vote_id(self, obj):
        if obj.source == 'consultation_platform':
            return obj.cp_id
        else:
            return obj.sn_id
    vote_id.short_description = 'Id'

    def vote_source(self, obj):
        if obj.source_consultation:
            return obj.source_consultation.name.title()
        else:
            return obj.source_social.name.title()
    vote_source.short_description = 'Source'

admin.site.register(ConsultationPlatform, ConsultationPlatformAdmin)
admin.site.register(Initiative, InitiativeAdmin)
admin.site.register(Campaign, CampaignAdmin)
admin.site.register(SocialNetwork, SocialNetworkAdmin)
admin.site.register(Idea, IdeaAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Vote, VoteAdmin)