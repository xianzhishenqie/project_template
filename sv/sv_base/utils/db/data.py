
SUB_MODEL_DELIMITER = '__'


def get_sub_model_data(data, sub_model_names):
	sub_model_data = {}
	prefix = SUB_MODEL_DELIMITER.join(sub_model_names + [''])
	for key in data:
		if key.startswith(prefix):
			sub_model_data[key[len(prefix):]] = data[key]

	return sub_model_data