
from sv_base.utils.models.common import get_obj
from sv_auth.models import User


def get_user(user):
    return get_obj(user, User)
