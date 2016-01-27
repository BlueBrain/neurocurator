#!/usr/bin/python3

__author__ = 'oreilly'
__email__  = 'christian.oreilly@epfl.ch'

import sys
from PySide import QtGui, QtCore
from SPARQLWrapper import SPARQLWrapper, JSON # install e.g. with pip install SPARQLWrapper
from Bio import Entrez
import pickle
import urllib

def build_request(queryHeader = "prefix xsd: <http://www.w3.org/2001/XMLSchema#> \n prefix property: <http://neurolex.org/wiki/Property-3A>",
                  querySelect = "select DISTINCT ?name ?id where",
                  where_list = []):

	return queryHeader + querySelect + '{' + ' . '.join(where_list) + '}'


def flatten_list(l):
    return [item for sublist in l for item in sublist]


def find_all_items(maxAttemps=10):

	where_list = ['?x property:Label ?name',
				  '?x property:Id ?id']
	try:
		sparql = SPARQLWrapper("http://rdf-stage.neuinfo.org/ds/query")
		sparql.setQuery(build_request(where_list=where_list))
		sparql.setReturnFormat(JSON)
		results = sparql.query().convert()
		return {result["id"]["value"]:result["name"]["value"] for result in results["results"]["bindings"]}
	except urllib.error.URLError:
		return find_all_items(maxAttemps)


def find_subregions(region_id, attempt=0, maxAttemps=10):

	where_list = [
		'?x property:Id "{0}"^^xsd:string'.format(region_id),
		'{?regions property:SuperCategory ?x_name} UNION { ?regions property:Is_part_of ?x }',
		'?regions property:Label ?name',
		'?x       property:Label ?x_name',
		'?regions property:Id ?id']

	try:
		sparql = SPARQLWrapper("http://rdf-stage.neuinfo.org/ds/query")
		sparql.setQuery(build_request(where_list=where_list))
		sparql.setReturnFormat(JSON)
		results = sparql.query().convert()
		return [result["id"]["value"] for result in results["results"]["bindings"]]
	except urllib.error.URLError:
		return find_subregions(region_id, attempt+1, maxAttemps)



def name_from_id(region_id, attempt=0, maxAttemps=10):

	where_list = ['?x property:Id "{0}"^^xsd:string'.format(region_id), '?x property:Label ?name',]

	try:
		sparql = SPARQLWrapper("http://rdf-stage.neuinfo.org/ds/query")
		sparql.setQuery(build_request(where_list=where_list))
		sparql.setReturnFormat(JSON)
		results = sparql.query().convert()
		return [result["name"]["value"] for result in results["results"]["bindings"]][0]
	except urllib.error.URLError:
		return name_from_id(region_id, attempt+1, maxAttemps)








class TreeData():
	def __init__(self, txt, id, parent=None, root_no=None):

		self.txt = txt
		self.id  = id
		self.parent = parent
		self.child = []
		self.icon = None
		self.index = None
		self.root_no = root_no


	def position(self):
		if self.parent is not None:
			for count, child in enumerate(self.parent.child):
				if child == self:
					return count
		else:
			return self.root_no



	@staticmethod
	def rebuild(root_ids, maxDepth=100, verbose=False):

		rebuild_tree(root_ids, maxDepth=100, verbose=False)
		rebuild_dic()

	@staticmethod
	def rebuild_tree(root_ids, maxDepth=100, verbose=False):

		def addSubtree(root, depth=0):
			if depth+1 < maxDepth: 
				for region_id in find_subregions(root.id):
					region_name = name_from_id(region_id).encode("ascii").decode("ascii")

					if verbose:
						print(" "*(depth+1) + region_name)

					child = TreeData(region_name, region_id, root)
					addSubtree(child, depth+1)
					root.child.append(child)

		roots = []
		for root_no, root_id in enumerate(root_ids):
			root_name = name_from_id(root_id).encode("ascii").decode("ascii")
			if verbose:
				print(root_name)

			root = TreeData(root_name, root_id, root_no=root_no)
			addSubtree(root)
			roots.append(root)

		with open("onto.tree", 'wb') as f:
			pickle.dump(roots, f)


	@staticmethod
	def rebuild_dic():
		with open("onto.dic", 'wb') as f:
			pickle.dump(find_all_items(), f)



	@staticmethod
	def load(fileName="onto.tree", fileNameDic="onto.dic"):
		with open(fileName, 'rb') as f:
			tree = pickle.load(f)
		with open(fileNameDic, 'rb') as f:
			dic = pickle.load(f)
		return tree, dic






#-------------------------------------------------------------------------------
#class TreeModel(QtGui.QStandardItemModel):
class TreeModel(QtCore.QAbstractItemModel):

	#---------------------------------------------------------------------------
	def __init__(self, tree):
		super(TreeModel, self).__init__()
		self.__tree = tree
		self.__current = tree[0]

	#---------------------------------------------------------------------------
	def flags(self, index):
		flag = QtCore.Qt.ItemIsEnabled
		if index.isValid():
		    flag |= QtCore.Qt.ItemIsSelectable
		return flag

	#---------------------------------------------------------------------------
	def index(self, row, column, parent=QtCore.QModelIndex()):
		if parent.isValid():
			node = parent.internalPointer().child[row]
		else:
			node = self.__tree[row]
		return self.__createIndex(row, column, node)

	#---------------------------------------------------------------------------
	def parent(self, index):
		node = QtCore.QModelIndex()
		if index.isValid():
		    nodeS = index.internalPointer()
		    parent = nodeS.parent
		    if parent is not None:
		        node = self.__createIndex(parent.position(), 0, parent)
		return node

	#---------------------------------------------------------------------------
	def rowCount(self, index=QtCore.QModelIndex()):
		count = len(self.__tree)
		node = index.internalPointer()
		if node is not None:
		    count = len(node.child)
		return count

	#---------------------------------------------------------------------------
	def columnCount(self, index=QtCore.QModelIndex()):
		return 1

	#---------------------------------------------------------------------------
	def data(self, index, role=QtCore.Qt.DisplayRole):
		data = None
		if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
		    node = index.internalPointer()
		    data = node.txt

		if role == QtCore.Qt.UserRole:
		    node = index.internalPointer()
		    data = node.id

		if role == QtCore.Qt.ToolTipRole:
		    node = index.internalPointer()
		    data = "ToolTip " + node.txt

		if role == QtCore.Qt.DecorationRole:
		    data = QtGui.QIcon("icon.png")
		return data

	#---------------------------------------------------------------------------
	def setData(self, index, value, role=QtCore.Qt.DisplayRole):
		result = True
		if role == QtCore.Qt.EditRole and value != "":
		    node = index.internalPointer()
		    node.text = value
		    result = True
		return result

	#---------------------------------------------------------------------------
	def __createIndex(self, row, column, node):
		if node.index == None:
		    index = self.createIndex(row, column, node)
		    node.index = index
		    icon = QtGui.QIcon("icon.png")
		    b = self.setData(index, icon, QtCore.Qt.DecorationRole)
		    b = self.setData(index, "ToolTip "+node.txt, QtCore.Qt.ToolTipRole)
		return node.index





	def headerData(self, section, orientation, role):
		if role == QtCore.Qt.DisplayRole:
			return None #"Neurolex tags"
		else:
			return None




#-------------------------------------------------------------------------------
class TreeView(QtGui.QTreeView):
	#---------------------------------------------------------------------------
	def __init__(self, model, parent=None):
		super(TreeView, self).__init__(parent)
		self.__model = model
		self.setModel(model)

		self.header().hide() 


		self.setCurrentIndex(self.__model.index(0, 0))
		return



if __name__ == "__main__":

	# As per Hierarchies listed on http://neurolex.org/wiki/Main_Page on November 16, 2015
	roots = {
		"Brain Regions":"birnlex_796",
		"Behavioral activity":"birnlex_1827",
		"Behavioral Paradigms":"birnlex_2075",
		"Brain Regions":"birnlex_796",
		"Diseases":"birnlex_11013",
		"Protocols":"OBI_0000272",
		"Imaging protocols":"birnlex_2126",
		"Molecules":"birnlex_22",
		"Cells":"sao1813327414",
		"Nervous System Function":"birnlex_2501",
		"Resource Types":"nlx_res_20090101",
		"Qualities":"PATO_0000001"}
	##		",
	##	"Subcellular Parts":"GO:0005575",

	TreeData.rebuild(sorted(list(roots.values())), maxDepth = 100, verbose = True)
	TreeData.rebuild_dic()


