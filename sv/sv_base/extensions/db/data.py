SUB_MODEL_DELIMITER = '__'


def get_sub_model_data(data, sub_model_names):
    """获取关联子对象数据

    :param data: 数据
    :param sub_model_names: 子对象关联层级名称
    :return: 子对象数据
    """
    sub_model_data = {}
    prefix = SUB_MODEL_DELIMITER.join(sub_model_names + [''])
    for key in data:
        if key.startswith(prefix):
            sub_model_data[key[len(prefix):]] = data[key]

    return sub_model_data
