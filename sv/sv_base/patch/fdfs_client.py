"""
fdfs_client补丁

"""
from fdfs_client.tracker_client import Storage_info, Tracker_client


_storage_info_set_info_default = Storage_info.set_info


def storage_info_set_info(self, o):
    """
    补丁，greendns补丁无法解析bytes类型ip地址
    """
    result = _storage_info_set_info_default(self, o)
    if isinstance(self.ip_addr, bytes):
        self.ip_addr = self.ip_addr.decode('utf-8')

    return result


_tracker_client_tracker_query_storage_stor_without_group_default = \
    Tracker_client.tracker_query_storage_stor_without_group


def tracker_client_tracker_query_storage_stor_without_group(self):
    """
    补丁，greendns补丁无法解析bytes类型ip地址
    """
    store_serv = _tracker_client_tracker_query_storage_stor_without_group_default(self)
    if isinstance(store_serv.ip_addr, bytes):
        store_serv.ip_addr = store_serv.ip_addr.decode('utf-8')

    return store_serv


_tracker_client_tracker_query_storage_stor_with_group_default = \
    Tracker_client.tracker_query_storage_stor_with_group


def tracker_client_tracker_query_storage_stor_with_group(self):
    """
    补丁，greendns补丁无法解析bytes类型ip地址
    """
    store_serv = _tracker_client_tracker_query_storage_stor_with_group_default(self)
    if isinstance(store_serv.ip_addr, bytes):
        store_serv.ip_addr = store_serv.ip_addr.decode('utf-8')

    return store_serv


_tracker_client__tracker_do_query_storage_default = Tracker_client._tracker_do_query_storage


def tracker_client__tracker_do_query_storage(self, group_name, filename, cmd):
    store_serv = _tracker_client__tracker_do_query_storage_default(self, group_name, filename, cmd)
    if isinstance(store_serv.ip_addr, bytes):
        store_serv.ip_addr = store_serv.ip_addr.decode('utf-8')

    return store_serv


def monkey_patch():
    """
    打补丁
    """
    Storage_info.set_info = storage_info_set_info
    Tracker_client.tracker_query_storage_stor_without_group = tracker_client_tracker_query_storage_stor_without_group
    Tracker_client.tracker_query_storage_stor_with_group = tracker_client_tracker_query_storage_stor_with_group
    Tracker_client._tracker_do_query_storage = tracker_client__tracker_do_query_storage
