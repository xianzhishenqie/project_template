from typing import Union, Optional

from sv_base.utils.db.common import get_obj
from sv_auth.models import User


def get_user(user: Union[User, int]) -> Optional[User]:
    return get_obj(user, User)
