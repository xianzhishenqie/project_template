from typing import Union, Optional

from sv_base.extensions.db.common import get_obj
from sv_auth.models import User


def get_user(user: Union[User, int]) -> Optional[User]:
    """获取用户数据对象

    :param user: 用户id或用户对象（不确定参数）
    :return: 用户对象
    """
    return get_obj(user, User)
