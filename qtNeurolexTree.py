#!/usr/bin/python3

__author__ = 'oreilly'
__email__  = 'christian.oreilly@epfl.ch'

from PySide import QtGui, QtCore
from SPARQLWrapper import SPARQLWrapper, JSON # install e.g. with pip install SPARQLWrapper
import pickle
import os
import urllib
from glob import glob
import pandas as pd
from scigraph_client import Vocabulary, Graph
from tag import nlx2ks




def build_request(queryHeader = "prefix xsd: <http://www.w3.org/2001/XMLSchema#> \n prefix property: <http://neurolex.org/wiki/Property-3A>",
                  querySelect = "select DISTINCT ?name ?id where",
                  where_list = []):

    return queryHeader + querySelect + '{' + ' . '.join(where_list) + '}'


def flatten_list(l):
    return [item for sublist in l for item in sublist]


def find_all_items(attempt=0, maxAttemps=10):

    where_list = ['?x property:Label ?name',
                  '?x property:Id ?id']
    try:
        sparql = SPARQLWrapper("http://rdf-stage.neuinfo.org/ds/query")
        sparql.setQuery(build_request(where_list=where_list))
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        return {result["id"]["value"]:result["name"]["value"] for result in results["results"]["bindings"]}
    except urllib.error.URLError:
        print("Raising cancelled.")
        if attempt == maxAttemps:
            raise
        else:
            return find_all_items(attempt+1)



def find_subregions(region_id, attempt=0, maxAttemps=10):

    where_list = [
        '?region property:Id "{0}"^^xsd:string'.format(region_id),
        '?subregions property:Is_part_of ?region_name',
        '?subregions property:Label ?subregions_name',
        '?region       property:Label ?region_name',
        '?subregions property:Id ?subregions_id']  
  
     #             [
    #    '?x property:Id "{0}"^^xsd:string'.format(region_id),
    #    '{?regions property:SuperCategory ?x_name} UNION { ?regions property:Is_part_of ?x }',
    #    '?regions property:Label ?name',
    #    '?x       property:Label ?x_name',
    #    '?regions property:Id ?id']
  
    try:
        sparql = SPARQLWrapper("http://rdf-stage.neuinfo.org/ds/query")
        sparql.setQuery(build_request(where_list=where_list))
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        return [result["subregions_id"]["value"] for result in results["results"]["bindings"]]
    except urllib.error.URLError:
        if attempt == maxAttemps:
            raise
        else:
            return find_subregions(region_id, attempt+1, maxAttemps)





def find_subcategories(cat_id, attempt=0, maxAttemps=10):

    where_list = [
        '?cat property:Id "{0}"^^xsd:string'.format(cat_id),
        '?subcats property:SuperCategory ?cat_name',
        '?subcats property:Label         ?subcats_name',
        '?cat     property:Label         ?cat_name',
        '?subcats property:Id            ?subcats_id']  
  
    try:
        sparql = SPARQLWrapper("http://rdf-stage.neuinfo.org/ds/query")
        sparql.setQuery(build_request(where_list=where_list))
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        return [result["subcats_id"]["value"] for result in results["results"]["bindings"]]
    except urllib.error.URLError:
        if attempt == maxAttemps:
            raise
        else:
            return find_subcategories(cat_id, attempt+1, maxAttemps)






def name_from_id(region_id, attempt=0, maxAttemps=10):

    where_list = ['?x property:Id "{0}"^^xsd:string'.format(region_id), '?x property:Label ?name',]

    try:
        sparql = SPARQLWrapper("http://rdf-stage.neuinfo.org/ds/query")
        sparql.setQuery(build_request(where_list=where_list))
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        return [result["name"]["value"] for result in results["results"]["bindings"]][0]
    except urllib.error.URLError:
        if attempt == maxAttemps:
            raise
        else:
            return name_from_id(region_id, attempt+1, maxAttemps)







class TreeData():
    def __init__(self, txt, id, parent=None, root_no=None):

        self.txt = txt
        self.id  = id
        self.parent = parent
        self.children = []
        self.icon = None
        self.index = None
        self.root_no = root_no


    def position(self):
        if self.parent is not None:
            for count, child in enumerate(self.parent.children):
                if child == self:
                    return count
        else:
            return self.root_no

    def isInTree(self, id):
        if id == self.id:
            return True
        elif id in nlx2ks:
            if nlx2ks[id] == self.id:
                return True
            
        for child in self.children:
            if child.isInTree(id):
                return True
        return False


    def getSubTree(self, id):
        if id == self.id:
            return self
        elif id in nlx2ks:
            if nlx2ks[id] == self.id:
                return self
            
        for child in self.children:
            subTree = child.getSubTree(id)
            if not subTree is None :
                return subTree
        return None



    def asList(self):
        idList   = [self.id]
        nameList = [self.txt]
        for child in self.children:
            ids, names = child.asList()
            idList.extend(ids)
            nameList.extend(names)
        return idList, nameList




    def printTree(self, level = 0):
        print("="*level + " " + self.txt)
        for child in self.children:
            child.printTree(level+1)







    @staticmethod
    def rebuild(root_ids, maxDepth=100, verbose=False, fileName="onto"):
        TreeData.rebuild_tree(root_ids, maxDepth=maxDepth, verbose=verbose, fileName=fileName)
        TreeData.rebuild_dic(fileName=fileName)
        


    @staticmethod
    def rebuildTreeFromKS(maxDepth=100, verbose=False, fileName="onto", recompute=True):
        vocab = Vocabulary()
        graph = Graph()            



        def addSubtree(root, depth=0): 
            if depth+1 < maxDepth:
                if root is None:
                    return
                neighbors = graph.getNeighbors(root.id, relationshipType="subClassOf", direction="INCOMING")
                if neighbors is None:
                    nodes = []
                else:
                    nodes = neighbors["nodes"]
                for node in nodes:
                    nodeLabel = node["lbl"]
                    nodeId    = node["id"]
                    
                    if root.id == nodeId:
                        continue
                    #print(list(node.keys()))
                    #print(node["lbl"])
                    if nodeLabel is None:
                        continue
                    
                    child = TreeData(nodeLabel, nodeId, root)            
                    termDic[nodeId] = nodeLabel
                    if verbose:
                        print(" "*(depth+1) + nodeLabel)
                    addSubtree(child, depth+1)
                    root.children.append(child)


        categories = vocab.getCategories()
        
        root_ids = []
        for cat in categories:
            catTerms = vocab.findByTerm(cat)
            if catTerms is None:
                continue
            for catTerm in catTerms :
                root_ids.append(catTerm["curie"])

        # Supplementary tree roots not included in categories
        root_ids.extend(["NIFMOL:nifext_8054", "BFO:0000023", "BIRNOBI:birnlex_11009", "NIFMOL:birnlex_15"])

        for root_no, root_id in enumerate(root_ids):
            
            # > 1, >10, >20, >30  [total <= 40, 1 skipped; ]
            if root_no > 34:
                termDic = {}            
                root = vocab.findById(root_id)
                if root is None:
                    continue
                if root["labels"] is None:
                    continue
                neighbors = graph.getNeighbors(root_id, relationshipType="subClassOf", direction="INCOMING")    
                if neighbors is None:
                    continue
                if len(neighbors["nodes"]) == 1:
                    continue
                
                root_name = root["labels"][0]
                if not recompute:
                    if (os.path.isfile(fileName + "_" + root_name + "_" + str(root_no) + ".tree") and
                        os.path.isfile(fileName + "_" + root_name + "_" + str(root_no) + ".dic")) :
                        continue
                    
                if verbose:
                    print(root_name)
                root = TreeData(root_name, root_id, root_no=root_no)            
                termDic[root_id] = root_name
                addSubtree(root)
    
    
                with open(fileName + "_" + root_name + "_" + str(root_no) + ".tree", 'wb') as f:
                    pickle.dump(root, f)
                with open(fileName + "_" + root_name + "_" + str(root_no) + ".dic", 'wb') as f:
                    pickle.dump(termDic, f)            







    

    @staticmethod
    def rebuild_tree(root_ids, maxDepth=100, verbose=False, fileName="onto"):
        logFileName = "failedEntity.log"

        def addSubtree(root, depth=0): 
            if depth+1 < maxDepth:
                try:                
                    subcategoryIds = find_subcategories(root.id)                
                except:
                    with open(logFileName, 'a') as f:
                        f.write("Failed to add the entity, find_subcategories failure, " + root.id + "\n")                
                else:
                    for region_id in subcategoryIds:
                        try:
                            region_name = name_from_id(region_id).encode("ascii", errors="ignore").decode("ascii", errors="ignore")
                        except:
                            with open(logFileName, 'a') as f:
                                f.write("Failed to add the entity, name_from_id_failure, " + region_id + "\n")
                        else:
                            if verbose:
                                print(" "*(depth+1) + region_name)
    
                            child = TreeData(region_name, region_id, root)
                            addSubtree(child, depth+1)
                            root.children.append(child)


        roots = []
        for root_no, root_id in enumerate(root_ids):

            try:
                root_name = name_from_id(root_id).encode("ascii", errors="ignore").decode("ascii", errors="ignore")
            except:
                with open(logFileName, 'a') as f:
                    f.write("Failed to add the entity, name_from_id_failure, " + root_id + "\n")                
            else:
                if verbose:
                    print(root_name)
    
                root = TreeData(root_name, root_id, root_no=root_no)
                addSubtree(root)
                roots.append(root)


        with open(fileName + ".tree", 'wb') as f:
            pickle.dump(roots, f)
            

    @staticmethod
    def rebuild_dic(fileName = "onto"):
        with open(fileName + ".dic", 'wb') as f:
            pickle.dump(find_all_items(), f)


    """

    @staticmethod
    def load(fileName="onto.tree", fileNameDic="onto.dic"):
        with open(fileName, 'rb') as f:
            tree = pickle.load(f)
        with open(fileNameDic, 'rb') as f:
            dic = pickle.load(f)
        #with open("neurolex.dic", 'rb') as f:
        #    dic.update(pickle.load(f))
        return tree, dic

    """



"""
 Better not to define as a TreeData static method because it cause problem
 when loading from pickle since pickle need to know the definition of the 
 class, which can be not loaded yet.
"""
def loadTreeData(fileNamePattern="onto/onto*"):
    from tag import nlx2ks 
    import collections
    # From http://stackoverflow.com/a/3387975/1825043
    class TransformedDict(collections.MutableMapping):
        """A dictionary that applies an arbitrary key-altering
           function before accessing the keys"""
    
        def __init__(self, *args, **kwargs):
            self.store = dict()
            self.update(dict(*args, **kwargs))  # use the free update to set keys
    
        def __getitem__(self, key):
            return self.store[self.__keytransform__(key)]
    
        def __setitem__(self, key, value):
            self.store[self.__keytransform__(key)] = value
    
        def __delitem__(self, key):
            del self.store[self.__keytransform__(key)]
    
        def __iter__(self):
            return iter(self.store)
    
        def __len__(self):
            return len(self.store)
    
        def __keytransform__(self, key):
            return key        


    class TranslatingDict(TransformedDict):
    
        def __keytransform__(self, id):
            return nlx2ks[id] if id in nlx2ks else id
    

 
 
    trees = []       
    for fileName in glob(fileNamePattern + ".tree"):
        with open(fileName, 'rb') as f:
            trees.append(pickle.load(f))
            
    dic = TranslatingDict()
    for fileName in glob(fileNamePattern + ".dic"):
        with open(fileName, 'rb') as f:
            dic.update(pickle.load(f))


    trees, dic = appendAdditions(trees, dic)
    dic = addSuppTerms(dic)
    return trees, dic



def addSuppTerms(dic):
    
    
    # Previously, we were doing something like...
    #    
    #idsToAdd = [...]
    #vocab = Vocabulary()
    #for id in idsToAdd:
    #    term = vocab.findById(id)      
    #    dic[id] = term["labels"][0] 
    #
    # ...but this calls the SciGraph interface which queries for the information
    # online. This fails when working offline. Thus, for now, we just specify
    # the terms name by hand.
    
    idsToAdd = {"NIFINV:birnlex_2300"   :"Computational model", 
                "GO:0030431"            :"sleep", 
                "NIFMOL:sao1797800540"  :"Sodium Channel",
                "NIFMOL:sao1846985919"  :"Calcium Channel", 
                "NIFGA:nlx_anat_1010"   :"Afferent role", 
                "NIFCELL:nifext_156"    :"Hippocampal pyramidal cell",
                "NIFMOL:sao940366596"   :"Ion Channel"}

    dic.update(idsToAdd)
    
    # These terms were in Neurolex but have not been ported to KS.
    orphanTerms = {"nlx_78803":"Burst Firing Pattern", 
                   "nlx_52865":"Modelling",
                   "nlx_152236":"Electron microscopy immunolabeling protocol"}
    dic.update(orphanTerms)
    
    return dic
    


def appendAdditions(treeData, dicData ):
    #inv_dicData = {v: k for k, v in dicData.items()}

    df = pd.read_csv("additionsToNeurolex.csv", skip_blank_lines=True, comment="#", 
                     delimiter=";", names=["id", "label", "definition", "superCategory", "synonyms"])

    for index, row in df.iterrows():
        if row["id"] in dicData:
            continue

        dicData[row["id"]] = row["label"]
        subTree = None
        for tree in treeData:
            subTree = tree.getSubTree(row["superCategory"])    
            if not subTree is None:
                break
        if subTree is None:
            raise ValueError
        child = TreeData(row["label"], row["id"], parent=subTree.id)
        subTree.children.append(child)


    #with open("onto.tree", 'wb') as f:
    #    pickle.dump(treeData, f)
    
    #with open("onto.dic", 'wb') as f:
    #    pickle.dump(dicData, f)

    return treeData, dicData






class TreeModel(QtCore.QAbstractItemModel):

    def __init__(self, tree):
        super(TreeModel, self).__init__()
        self.__tree = tree
        self.__current = tree[0]


    def flags(self, index):
        flag = QtCore.Qt.ItemIsEnabled
        if index.isValid():
            flag |= QtCore.Qt.ItemIsSelectable
        return flag


    def index(self, row, column, parent=QtCore.QModelIndex()):
        if parent.isValid():
            node = parent.internalPointer().children[row]
        else:
            node = self.__tree[row]
        return self.__createIndex(row, column, node)


    def parent(self, index):
        node = QtCore.QModelIndex()
        if index.isValid():
            nodeS = index.internalPointer()
            parent = nodeS.parent
            if parent is not None:
                node = self.__createIndex(parent.position(), 0, parent)
        return node


    def rowCount(self, index=QtCore.QModelIndex()):
        count = len(self.__tree)
        node = index.internalPointer()
        if node is not None:
            count = len(node.children)
        return count


    def columnCount(self, index=QtCore.QModelIndex()):
        return 1


    def data(self, index, role=QtCore.Qt.DisplayRole):
        data = None
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            node = index.internalPointer()
            data = node.txt

        if role == QtCore.Qt.UserRole:
            node = index.internalPointer()
            data = node.id

        return data


    def setData(self, index, value, role=QtCore.Qt.DisplayRole):
        result = True
        if role == QtCore.Qt.EditRole and value != "":
            node = index.internalPointer()
            node.text = value
            result = True
        return result


    def __createIndex(self, row, column, node):
        if node.index == None:
            index = self.createIndex(row, column, node)
            node.index = index
        return node.index

    def headerData(self, section, orientation, role):
        return None





class TreeView(QtGui.QTreeView):

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
        "Qualities":"PATO_0000001",
        "Entity":"Entity"}
    ##        ",
    ##    "Subcellular Parts":"GO:0005575",


    ####TreeData.rebuild(sorted(list(roots.values())), maxDepth = 100, verbose = True)
    #TreeData.rebuild(sorted(list(roots.values())), maxDepth = 1000, verbose = True, fileName="test")
    #appendAdditions()


    # Categories from
    #vocab = Vocabulary()
    #vocab.getCategories():
    #  "technique":"ERO:0000007",
    #  "biological process", # None found
    #  "Resource":"NIFRES:nlx_res_20090101",
    #  "cell":"NIFCELL:sao1813327414",    # rejected "NEMO:9559000" and "GO:0005623"
    #  "disease": [BIRNOBI:birnlex_11013", "DOID:4"] # rejected "OBO:OBI_1110055"
    #  "Institution":[":birnlex_2085", "NIFINV:birnlex_2085", "NEMO:1725000"]
    #  "organism":"OBO:OBI_0100026",  #  or "NIFORG:birnlex_2"
    #  "University": ":NEMO_0569000", # or "NEMO:0569000"
    #  "molecular entity":"OBO:CHEBI_23367", # or "OLD_CHEBI:23367"
    #  "GovernmentAgency",
    #  "anatomical entity": "UBERON:0001062", # or "NIFGA:birnlex_6"
    #  "quality",
    #  "subcellular entity"



    TreeData.rebuildTreeFromKS(maxDepth=100, verbose=True, fileName="onto/onto", recompute=False)



