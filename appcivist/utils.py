from appcivist.models import Assembly

def updateAssembliesSessionKeys():
    assemblies = Assembly.objects.all()
    for assembly in assemblies:
        if assembly.keyAboutToExpire():
            print("SI VA A CAMBIAR")
            assembly.updateSessionKey()
        else:
            print("NO VA A CAMBIAR")
