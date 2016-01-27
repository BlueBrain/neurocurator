#!/usr/bin/python3

__author__ = "Christian O'Reilly"

from PySide import QtGui, QtCore
import quantities as pq


def unitIsValid(unit):
	try:
		pq.Quantity(1, unit)
	except:
		return False
	return True



def getParameterTypes(fileName = "modelingDictionary.csv"):
	with open(fileName, 'r') as f:
		lines = f.readlines()
	return [ParameterType.readIn(line) for line in lines if line.strip() != ""]

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


class ParameterType:

	def __init__(self):
		self.ID 			= None
		self.name  			= None
		self.description	= None

		self.parseStr   = '"{}";"{}";"{}"'

	@staticmethod
	def readIn(paramStr):
		parameter = ParameterType()
		paramStr 						= paramStr.split('\n')[0]
		parameter.ID, parameter.name, parameter.description = paramStr.split('";"')
		parameter.ID 					= parameter.ID[1:]
		parameter.description 			= parameter.description[:-1]
		return parameter

	def __repr__(self):
		return self.__str__()

	def __str__(self):
		return self.parseStr.format(self.ID, self.name, self.description)




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








class ParameterInstance (AbstractParameterInstance):
	# This class represent a parameter instance. It can be used to 
	# represent 1) a parameter that is specified in a
	# modeling file (e.g. .mm_py, .mm_hoc, .mm_mod) with the #|...|# 
	# formalism or 2) a parameter specified by a given annotation.
	# The objects encode the type of parameter, its numerical value,
  	# the units in which it is specified, and the annotation and publication
	# ID it refers to. 

	def __init__(self, typeID):
		super(ParameterInstance, self).__init__()
		self.typeID	 		= typeID
		self.__annotID		= None
		self.__pubID		= None
		self.requirements 	= []

		self.parseStr   = '"{}";"{}";{};"{}";"{}";{}'


	def toJSON(self):
		return {"id":self.typeID, "unit":self.unit, "value":self.value}

	@staticmethod	
	def fromJSON(jsonParams):
		params = []
		for jsonParam in jsonParams:		
			param = ParameterInstance(jsonParam["id"])
			param.setValue(jsonParam["value"], jsonParam["unit"])
			params.append(param)
		return params




	def setAnnotation(self, annotID, pubID):
		# Technically, only the annotId would need to be stored since it is 
		# unique and can therefore be traced. However, for convenience, we always
		# accompany it from its pubID since annotations are recorded in separate files
		# which are specified according to pubID. Thus, having the pubID facilitate 
		# finding the annotation.
		self.__annotID 	= annotID
		self.__pubID	= pubID



	def __repr__(self):
		return self.__str__()

	def __str__(self):
		return self.parseStr.format(self.typeID, self.unit, self.value, self.__annotID, self.__pubID, self.requirements)


	@property
	def name(self):
		return getParameterTypeNameFromID(self.typeID)

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







class CustomParameterInstance (AbstractParameterInstance):

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

	def __init__(self, parent, parameterList = [], header = ['Name', 'Value', 'Unit'], *args):
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
			return getParameterTypeNameFromID(param.typeID)
		elif ind == 1:
			return param.value
		elif ind == 2 :
			return param.unit
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

