
Filters = {
	'exact':'=',
	'lt':'<',
	'gt':'>',
	'lte':'<=',
	'gte':'>=',
	'contains':'LIKE'
}

def get_args(text):
	""" Get arguments from a filter string

		Expected Format: example__filtertype=value
		returns (example__filtertype,value)
	"""
	arg_tokens = text.split("=")
	if len(arg_tokens) != 2:
		raise Exception('invalid filter format',text)
	return arg_tokens

def get_vars(text):
	""" Get variables from an argument string

		Expected Format: example__filtertype
		returns (example,filtertype)
	"""
	var_tokens = text.split("__")
	if len(var_tokens) != 2:
		raise Exception('invalid filter format',text)
	return var_tokens

def get_filter(text):
	""" Return filter as a tuple of (field_name,filter_type,comparison_name)

		Args:
			text: String.  Format = example__filtertype=value

		Returns:
			(field_name,filter_type,comparison_name)

			field_name:  String.  Name of field to filter on
			filter_type:  String.  Type of filter
			comparison_name:  String.  Value for filter comparison.

		TODO:
			[1] - Filters should be more than strings, they should have classes
	"""


	arg_tokens = get_args(text)
	var_tokens = get_vars(arg_tokens[0])
	

	if len(var_tokens) != 2 or len(arg_tokens) != 2:
		raise Exception('invalid filter format',text)

	if var_tokens[1] not in Filters:
		raise Exception('invalid filter type',var_tokens[1])

	return (var_tokens[0],Filters[var_tokens[1]],arg_tokens[1])