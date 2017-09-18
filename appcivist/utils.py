from appcivist.models import Assembly

def updateAssembliesSessionKeys():
    assemblies = Assembly.objects.all()
    for assembly in assemblies:
        if assembly.keyHasExpired() or assembly.admin_session_key=="":
            assembly.updateSessionKey()
