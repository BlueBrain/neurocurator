#!/usr/bin/python3

__author__ = "Christian O'Reilly"

from PySide import QtGui, QtCore
import quantities as pq
import csv
from io import StringIO
from uuid import uuid1
from abc import abstractmethod
import pandas as pd

from tag import Tag, RequiredTag

statisticList  = ["raw", "mean", "median", "mode", "sem", "sd", "var", "CI_90", "CI_95", "CI_99", "N", "min", "max", "other"]
expFeatureList  = ["Temperature", "Age (days)", "Age (years)", "Junction potential correction"]

def unitIsValid(unit):
	try:
		pq.Quantity(1, unit)
	except:
		return False
	return True




class ParameterTypeTree:

	def __init__(self, value):
		if not isinstance(value, ParameterType):
			raise TypeError

		self.children = []	
		self.value	  = value

	def addChild(self, child):
		if not isinstance(child, ParameterTypeTree):
			raise TypeError

		self.children.append(child)


	def asList(self):
		paramTypeList = [value]
		for child in self.children:
			paramTypeList.extend(child.asList())
		return paramTypeList



	def isInTree(self, ID):
		if ID == self.value.ID:
			return True
		for child in self.children:
			if child.isInTree(ID):
				return True
		return False


	def getSubTree(self, ID):
		if ID == self.value.ID:
			return self
		for child in self.children:
			subTree = child.getSubTree(ID)
			if not subTree is None :
				return subTree
		return None



	def printTree(self, level = 0):
		print("="*level + " " + self.value.name)
		for child in self.children:
			child.printTree(level+1)


	@staticmethod
	def load(fileName = "modelingDictionary.csv", root = "BBP-000000"):

		def addChildren(tree, df):
			children = df[df["parentId"] == tree.value.ID]
			for index, row in children.iterrows():
				child = ParameterTypeTree(ParameterType(row["id"], row["parentId"], 
			 			row["name"], row["description"], eval(row["requiredTags"])))
				child = addChildren(child, df)
				tree.addChild(child)

			return tree

		df = pd.read_csv(fileName, skip_blank_lines=True, comment="#", 
						 delimiter=";", quotechar='"', 
						 names=["id", "parentId", "name", "description", "requiredTags"])


		row = df[df["id"] == root]		

		tree = ParameterTypeTree(ParameterType(row["id"][0], row["parentId"][0], 
					 			row["name"][0], row["description"][0], eval(row["requiredTags"][0])))

		return addChildren(tree, df)



def getParameterTypes(fileName = "modelingDictionary.csv"):
	with open(fileName, 'r') as f:
		lines = f.readlines()
	return [ParameterType.readIn(line) for line in lines if line.strip() != "" and line[0] != "#"]


def getParameterTypeNameFromID(ID, parameterTypes = None):
	if parameterTypes is None:
		parameterTypes = getParameterTypes()

	for param in parameterTypes:
		if param.ID == ID:
			return param.name

	return None


def getParameterTypeIDFromName(name, parameterTypes = None):
	if parameterTypes is None:
		parameterTypes = getParameterTypes()

	for param in parameterTypes:
		if param.name == name:
			return param.ID

	return None


def getParameterTypeFromID(ID, parameterTypes = None):
	if parameterTypes is None:
		parameterTypes = getParameterTypes()

	for param in parameterTypes:
		if param.ID == ID:
			return param

	return None


def getParameterTypeFromName(name, parameterTypes = None):
	if parameterTypes is None:
		parameterTypes = getParameterTypes()

	for param in parameterTypes:
		if param.name == name:
			return param

	return None





class Relationship:
	
	def __init__(self, type_, entity1, entity2):
		if not isinstance(type_, str):
			raise TypeError
		if not type_ in ["point", "directed", "undirected"]:
			raise ValueError
		if not isinstance(entity1, Tag):
			raise TypeError
		if type_ == "point":
			if not entity2 is None:
				raise ValueError
		elif not isinstance(entity2, Tag):
			raise TypeError

		self.type 		= type_   # A value in : ["point", "directed", "undirected"]

		self.entity1	= entity1 # for directed relationship, it is the "from" entity

		self.entity2	= entity2 # for directed relationship, it is the "to" entity
							      # for the point, it should keep a None value

	def __repr__(self):
		return str(self.toJSON())

	def __str__(self):
		return str(self.toJSON())

	def toJSON(self):
		if self.entity2 is None:
			return {"type":self.type, "entity1": self.entity1.toJSON(), "entity2":"None"}
		else:
			return {"type":self.type, "entity1": self.entity1.toJSON(), "entity2":self.entity2.toJSON()}

	@staticmethod
	def fromJSON(jsonString):
		return Relationship(jsonString["type"], Tag.fromJSON(jsonString["entity1"]), 
							None if jsonString["entity2"] == "None" else Tag.fromJSON(jsonString["entity2"]))




class ParameterType:

	def __init__(self, ID = None, parent = None, name = None, description = None, requiredTags = None):
		self.ID 			= ID
		self.parent			= parent
		self.name  			= name
		self.description	= description
		self.requiredTags	= requiredTags

		self.parseStr   = '"{}";"{}";"{}";"{}";{}'
		# ID;PARENT;NAME;DESCRIPTION;REQUIRED_TAGS



	@staticmethod
	def readIn(paramStr):
		parameter = ParameterType()
		reader = csv.reader(StringIO(paramStr) , delimiter=';') 
		try:
			parameter.ID, parameter.parent, parameter.name, parameter.description, parameter.requiredTags = [item.strip() for item in list(reader)[0]]
			parameter.requiredTags = eval(parameter.requiredTags)
		except ValueError:
			print("Problematic recording: ", paramStr)
			raise

		return parameter

	def __repr__(self):
		return self.__str__()

	def __str__(self):
		return self.parseStr.format(self.ID, self.parent, self.name, self.description, self.requiredTags)





class ExperimentProperty:


	def __init__(self, name, value, unit):
		if not isinstance(name, str):
			raise TypeError
		if not isinstance(value, float):
			raise Ty

		self.name		= name
		self.value		= value
		self.unit  		= unit

	@staticmethod	
	def fromJSON(jsonString):
		return ExperimentProperty(jsonString["name"], jsonString["value"], jsonString["unit"])

	def toJSON(self):
		return {"name": self.name, "value": self.value, "unit": self.unit}

	def __str__(self):
		return str(self.toJSON())

	def __repr__(self):
		return str(self.toJSON())





class Values:

	@staticmethod	
	def fromJSON(jsonString):
		if jsonString["type"] == "simple":
			return ValuesSimple.fromJSON(jsonString)
		elif jsonString["type"] == "compounded":
			return ValuesCompounded.fromJSON(jsonString)
		else:
			raise ValueError

	@abstractmethod
	def toJSON(self):
		raise NotImplementedError



class ValuesSimple(Values):

	def __init__(self, values, unit, statistic = "raw"):
		if not isinstance(values, list):
			raise TypeError

		self.values		= values
		self.unit  		= unit
		self.statistic  = statistic

	@staticmethod	
	def fromJSON(jsonString):
		if not jsonString["statistic"] in statisticList:
			raise ValueError("Invalid statistic '" + jsonString["statistic"] + "'. Statistics should take one of the following values: ", str(statisticList))

		return ValuesSimple(jsonString["values"], jsonString["unit"], jsonString["statistic"])

	def toJSON(self):
		return {"type": "simple", "values": self.values, "unit": self.unit, "statistic":self.statistic}

	def __str__(self):
		return str(self.toJSON())

	def __repr__(self):
		return str(self.toJSON())






class ValuesCompounded(Values):

	def __init__(self, valuesLst):
		if not isinstance(valuesLst, list):
			raise TypeError
		self.valueLst	= values

	@staticmethod	
	def fromJSON(jsonString):
		return ValuesCompounded([Values.fromJSON(v) for v in jsonString["valueLst"]])

	def toJSON(self):
		return {"type": "compounded", "valueLst": [v.toJSON() for v in self.values]}

	def __str__(self):
		return str(self.toJSON())

	def __repr__(self):
		return str(self.toJSON())








class NumericalVariable:

	def __init__(self, typeId, values):
		if not isinstance(typeId, str):
			raise TypeError
		if not isinstance(values, Values):
			raise TypeError


		self.typeId  	= typeId
		self.values		= values

	@staticmethod	
	def fromJSON(jsonString):
		return NumericalVariable(jsonString["typeId"], Values.fromJSON(jsonString["values"]))

	def toJSON(self):
		return {"typeId": self.typeId, "values": self.values.toJSON()}

	def __str__(self):
		return str(self.toJSON())

	def __repr__(self):
		return str(self.toJSON())






class Variable:

	def __init__(self, typeId, unit, statistic):
		self.typeId  	= typeId
		self.unit  		= unit
		self.statistic  = statistic

	@staticmethod	
	def fromJSON(jsonString):
		if not jsonString["statistic"] in statisticList:
			raise ValueError("Invalid statistic (" + jsonString["statistic"] + "). Statistics should take one of the following values: ", str(statisticList))

		return Variable(jsonString["typeId"], jsonString["unit"], jsonString["statistic"])

	def toJSON(self):
		return {"typeId": self.typeId, "unit": self.unit, "statistic":self.statistic}

	def __str__(self):
		return str(self.toJSON())

	def __repr__(self):
		return str(self.toJSON())








class ParamDesc:
	@staticmethod	
	@abstractmethod
	def fromJSON(jsonString):
		if jsonString["type"] == "function": 
			return ParamDescFunction.fromJSON(jsonString)
		elif jsonString["type"] == "numericalTrace": 
			return ParamDescTrace.fromJSON(jsonString)
		elif jsonString["type"] == "pointValue": 
			return ParamDescPoint.fromJSON(jsonString)
		else:
			raise ValueError

	@abstractmethod
	def toJSON(self):
		raise NotImplementedError







class ParamDescPoint(ParamDesc): 

	def __init__(self, depVar):
		if not isinstance(depVar, NumericalVariable):
			raise ValueError

		self.depVar  		= depVar
		self.type			= "pointValue"

	@staticmethod	
	def fromJSON(jsonString):
		return ParamDescPoint(NumericalVariable.fromJSON(jsonString["depVar"]))

	def toJSON(self):
		return {"type":"pointValue", "depVar": self.depVar.toJSON()}

	def __str__(self):
		return str(self.toJSON())

	def __repr__(self):
		return str(self.toJSON())




class ParamDescFunction(ParamDesc): 

	def __init__(self, depVar, indepVars, parameterIds, equation):
		if not isinstance(depVar, Variable):
			raise TypeError
		if not isinstance(indepVars, list):
			raise TypeError
		for item in indepVars:
			if not isinstance(item, Variable):
				raise TypeError
		if not isinstance(parameterIds, list):
			raise TypeError
		if not isinstance(equation, str):
			raise TypeError

		self.depVar  		= depVar
		self.indepVars   	= indepVars
		self.parameterIds   = parameterIds
		self.equation		= equation
		self.type			= "function"

	@staticmethod	
	def fromJSON(jsonString):
		return ParamDescFunction(Variable.fromJSON(jsonString["depVar"]), 
								[Variable.fromJSON(s) for s in jsonString["indepVars"]], 
								[ParameterInstance.fromJSON(s) for s in jsonString["parameterIds"]], 
								jsonString["equation"])

	def toJSON(self):
		return {"type":"function", "depVar": self.depVar.toJSON(), 
				"indepVars": [var.toJSON() for var in self.indepVars], 
				"parameterIds":[par.toJSON() for par in self.parameterIds], 
				"equation":self.equation}

	def __str__(self):
		return str(self.toJSON())

	def __repr__(self):
		return str(self.toJSON())






class ParamDescTrace(ParamDesc): 

	def __init__(self, depVar, indepVars):
		if not isinstance(depVar, NumericalVariable):
			raise TypeError
		if not isinstance(indepVars, list):
			raise TypeError
		for item in indepVars:
			if not isinstance(item, NumericalVariable):
				raise TypeError

		self.depVar  		= depVar
		self.indepVars   	= indepVars
		self.type			= "numericalTrace"

	@staticmethod	
	def fromJSON(jsonString):
		return ParamDescTrace(NumericalVariable.fromJSON(jsonString["depVar"]), 
							 [NumericalVariable.fromJSON(s) for s in jsonString["indepVars"]])

	def toJSON(self):
		return {"type":"numericalTrace", "depVar": self.depVar.toJSON(), 
				"indepVars": [var.toJSON() for var in self.indepVars]}

	def __str__(self):
		return str(self.toJSON())

	def __repr__(self):
		return str(self.toJSON())







class AbstractParameterInstance:
	# This class represent a parameter instance. It can be used to 
	# represent 1) a parameter that is specified in a
	# modeling file (e.g. .mm_py, .mm_hoc, .mm_mod) with the #|...|# 
	# formalism or 2) a parameter specified by a given annotation.
	# The objects encode the type of parameter, its numerical value,
  	# the units in which it is specified, and the annotation and publication
	# ID it refers to. 

	def __init__(self):
		self.__unit 		= None
		self.__value		= None

	def setValue(self, value, unit):
		# A value must always be set along with its unit. Else, it is meaningless. 
		self.__unit 	= unit
		self.__value	= value

	def convertUnit(self, unit):
		pass


	@property
	def unit(self):
		# Make unit validation
		return self.__unit

	@property
	def value(self):
		return self.__value




class ParameterInstance:
	# This class represent a parameter instance. It can be used to 
	# represent 1) a parameter that is specified in a
	# modeling file (e.g. .mm_py, .mm_hoc, .mm_mod) with the #|...|# 
	# formalism or 2) a parameter specified by a given annotation.
	# The objects encode the type of parameter, its numerical value,
  	# the units in which it is specified, and the annotation and publication
	# ID it refers to. 
	def __init__(self, id, description,
				 experimentProperties, requiredTags, relationship):
		super(ParameterInstance, self).__init__()


		if not isinstance(relationship, Relationship):
			raise ValueError
		if not isinstance(description, ParamDesc):
			raise ValueError
		if not isinstance(experimentProperties, list):
			raise ValueError
		for expProp in experimentProperties:
			if not isinstance(expProp, ExperimentProperty):
				raise ValueError
		if not isinstance(requiredTags, list):
			raise ValueError
		for reqTag in requiredTags:
			if not isinstance(reqTag, RequiredTag):
				raise ValueError

		if id is None:
			self.id = str(uuid1())
		else:
			self.id	= id

		self.requiredTags 			= requiredTags
		self.experimentProperties 	= experimentProperties
		self.description			= description
		self.relationship			= relationship



	def toJSON(self):
		print(self.requiredTags)
		return {"id":self.id, 
				"description":self.description.toJSON(), 
				"experimentProperties":[expProp.toJSON() for expProp in self.experimentProperties], 
				"requiredTags": [reqTag.toJSON() for reqTag in self.requiredTags], 
				"relationship":self.relationship.toJSON()}


	@property
	def unit(self):
		if isinstance(self.description.depVar, Variable):
			return self.description.depVar.unit
		elif isinstance(self.description.depVar, NumericalVariable):
			return self.description.depVar.values.unit
		else:
			raise TypeError


	@property
	def values(self):
		if isinstance(self.description.depVar, NumericalVariable):
			return self.description.depVar.values.values
		elif isinstance(self.description.depVar, Variable):
			return None
		else:
			raise TypeError


	@property
	def typeId(self):
		return self.description.depVar.typeId

	@property
	def typeDesc(self):
		return self.description.type


	@staticmethod	
	def fromJSON(jsonParams):
		params = []
		for jsonParam in jsonParams:
			
			if not "requiredTags" in jsonParam:
				# To convert older format annotations
				values 			= ValuesSimple([jsonParam["value"]], jsonParam["unit"])
				if jsonParam["id"] == "BBP-01104":
					typeId = "BBP-011001"
					requiredTags    = [RequiredTag("nifext_8055", "Sodium current", "nifext_8054"), RequiredTag("sao1813327414", "Cell", "sao1813327414")]				
					relationship 	= Relationship("point", Tag("nifext_8055", "Sodium current"), None)
				elif jsonParam["id"] == "BBP-01103":
					typeId = "BBP-011001"
					requiredTags = [RequiredTag("nifext_8056", "Potassium current", "nifext_8054"), RequiredTag("sao1813327414", "Cell", "sao1813327414")]
					relationship = Relationship("point", Tag("nifext_8056", "Potassium current"), None)
				elif jsonParam["id"] == "BBP-03003":
					typeId = "BBP-121003"
					requiredTags = [RequiredTag("sao1813327414", "Cell", "sao1813327414")]
					relationship = Relationship("point", Tag("sao1813327414", "Cell"), None)
				elif jsonParam["id"] == "BBP-03004":
					typeId = "BBP-121004"
					requiredTags = [RequiredTag("sao1813327414", "Cell", "sao1813327414")]
					relationship = Relationship("point", Tag("sao1813327414", "Cell"), None)
				elif jsonParam["id"] == "BBP-01001":
					typeId = "BBP-040001"
					requiredTags = [RequiredTag("sao1813327414", "Cell", "sao1813327414")]
					relationship = Relationship("point", Tag("sao1813327414", "Cell"), None)
				elif jsonParam["id"] == "BBP-01300":
					typeId = "BBP-022000"
					requiredTags = [RequiredTag("sao1813327414", "Cell", "sao1813327414")]
					relationship = Relationship("point", Tag("sao1813327414", "Cell"), None)
				elif jsonParam["id"] == "BBP-01402":
					typeId = "BBP-030001"
					requiredTags = [RequiredTag("BBP_nlx_0001", "Leak ionic current", "nifext_8054"), RequiredTag("sao1813327414", "Cell", "sao1813327414")]
					relationship = Relationship("point", Tag("BBP_nlx_0001", "Leak ionic current"), None)
				else:
					print(jsonParam["id"])
					print(jsonParam)
					print(getParameterTypeFromID(jsonParam["id"]))
					raise ValueError
				param = ParameterInstance(None, ParamDescPoint(NumericalVariable(typeId, values)),
										  [], requiredTags, relationship)
			else:
				print(jsonParams)
				param = ParameterInstance(jsonParam["id"],  #jsonParam["typeId"],
										  ParamDesc.fromJSON(jsonParam["description"]), 
										  [ExperimentProperty.fromJSON(s) for s in jsonParam["experimentProperties"]],
										  [RequiredTag.fromJSON(s) for s in jsonParam["requiredTags"]], 
										  Relationship.fromJSON(jsonParam["relationship"]))
			  
			params.append(param)

		return params



	"""
	def setAnnotation(self, annotID, pubID):
		# Technically, only the annotId would need to be stored since it is 
		# unique and can therefore be traced. However, for convenience, we always
		# accompany it from its pubID since annotations are recorded in separate files
		# which are specified according to pubID. Thus, having the pubID facilitate 
		# finding the annotation.
		self.__annotID 	= annotID
		self.__pubID	= pubID
	"""


	def __repr__(self):
		return str(self.__str__())

	def __str__(self):
		return str(self.toJSON())
		#return self.parseStr.format(self.typeID, self.unit, self.value, self.__annotID, self.__pubID, self.requirements)


	@property
	def name(self):
		return getParameterTypeNameFromID(self.typeId)

	"""
	@property
	def annotID(self):
		return self.__annotID


	@property
	def pubID(self):
		return self.__pubID


	def isComplete(self):
		# No need to check unit because value-units are always
		# set in pairs.
		if self.value is None:
			return False

		# No need to check paperID because paperID-annotID are always
		# set in pairs.
		if self.__annotID is None:
			return False

		return True


	@staticmethod
	def readIn(paramStr):

		paramStr 									= paramStr.split('\n')[0]
		typeID, str1, str2    						= paramStr.split('";"')
		typeID										= typeID[1:]
		parameter 									= ParameterInstance(typeID)


		unit, str1,              					= str1.split('";')
		value, parameter.__annotID      			= str1.split(';"')
		parameter.setValue(value, unit)

		parameter.__pubID, parameter.requirements 	= str2.split('";')

		return parameter
	"""

	@staticmethod
	def readIn(fileObject):
		try:
			return fromJSON(json.load(fileObject))
		except ValueError:
			if fileObject.read() == "":
				return []
			else:
				print("File content: ", fileObject.read())
				raise






class CustomParameterInstance (AbstractParameterInstance):
	#### TODO: NEED TO BE REDEFINED IN AGREEMENT WITH THE 
    ####       NEW CODE REFACTORING.


	def __init__(self, name, justification = None):
		super(CustomParameterInstance, self).__init__()
		self.name			= name
		self.justification 	= justification



	def isComplete(self):
		# No need to check unit because value-units are always
		# set in pairs.
		if self.value is None:
			return False

		if self.justification is None:
			return False

		return True









class ParameterListModel(QtCore.QAbstractTableModel):

	def __init__(self, parent, parameterList = [], header = ['Type', 'Description'], *args):
		QtCore.QAbstractTableModel.__init__(self, parent, *args)
		self.parameterList = parameterList
		self.header = header
		self.nbCol = len(header)

	def rowCount(self, parent=None):
		return len(self.parameterList)

	def columnCount(self, parent=None):
		return self.nbCol 


	def getSelectedParameter(self, selection):

		if isinstance(selection, list):
			if selection == []:
				return None
			elif isinstance(selection[0], QtCore.QModelIndex):
				index = selection[0]
		else:
			if selection.at(0) is None:
				return None
			index = selection.at(0).indexes()[0]
		return self.parameterList[index.row()]



	def getByIndex(self, param, ind):
		if ind == 0:
			return param.typeDesc
		elif ind == 1:
			if param.typeDesc == "pointValue":
				return "name:" + param.name + "; values:" + str(param.values)
			elif param.typeDesc == "function":
				return param.description.equation
			elif param.typeDesc == "numericalTrace":
				return getParameterTypeNameFromID(param.description.depVar.typeId) \
						  + "=f(" + " ,".join([getParameterTypeNameFromID(v.typeId) for v in param.description.indepVars]) +  ")"
			else:
				raise ValueError
		else:
			raise ValueError

	def data(self, index, role):
		if not index.isValid():
		    return None

		if role != QtCore.Qt.DisplayRole:
			return None

		return self.getByIndex(self.parameterList[index.row()], index.column())

	def headerData(self, col, orientation, role):
		if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
		    return self.header[col]
		return None

	def sort(self, col, order):
		"""sort table by given column number col"""
		self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
		reverse = (order == QtCore.Qt.DescendingOrder)
		self.annotationList = sorted(self.parameterList, key=lambda x: x.getByIndex(col), reverse = reverse) 
		self.emit(QtCore.SIGNAL("layoutChanged()"))

	def refresh(self):
		self.emit(QtCore.SIGNAL("layoutChanged()"))




