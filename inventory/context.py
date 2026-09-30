import os


def instance_name(request):
    return {"instance_name": os.environ.get("INSTANCE_NAME", "desarrollo")}
