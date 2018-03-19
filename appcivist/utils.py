from appcivist.models import Campaign

def updateAssembliesSessionKeys():
    campaigns = Campaign.objects.all()
    for campaign in campaigns:
        if campaign.keyHasExpired() or campaign.admin_session_key=="":
            campaign.updateSessionKey()
