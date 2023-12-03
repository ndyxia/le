from pyjsparser import parse as coparse

class Variable:
	def __init__(self, name, value):
		self.name = name
		self.value = value

def getJsVariables(jscode):
	tvar = []
	jsParsed = coparse(jscode)
	for element in jsParsed["body"]:
		if element["type"] == "VariableDeclaration":
			for declaration in element["declarations"]:
				if declaration["type"] == "VariableDeclarator":
					tvar.append(Variable(declaration["id"]["name"], declaration["init"]["value"]))
	return tvar
