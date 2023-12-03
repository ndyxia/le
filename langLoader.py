from yaml import safe_load

def langLoad(lang):
	try:
		return safe_load(open(f"lang/{lang}.yml", "r"))
	except FileNotFoundError:
		return safe_load(open(f"lang/en.yml", "r"))