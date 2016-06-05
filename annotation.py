#!/usr/bin/python3

__author__ = "Christian O'Reilly"

from uuid import uuid1
from PySide import QtGui, QtCore
#from parse import parse
import json
from abc import abstractmethod
from modelingParameter import ParameterInstance, ParamRef# ExperimentProperty
from tag import Tag
from restClient import RESTClient

import utils
from os.path import join, isfile

class Localizer:
    @staticmethod    
    @abstractmethod
    def fromJSON(jsonString):
        raise NotImplementedError

    @abstractmethod
    def toJSON(self):
        raise NotImplementedError

    


class TextLocalizer(Localizer):

    def __init__(self, text, start):
        self.text  = text
        self.start = start    

    @staticmethod    
    def fromJSON(jsonString):
        return TextLocalizer(jsonString["text"], jsonString["location"])

    def toJSON(self):
        return {"type":"text", "location": self.start, "text": self.text}

    def __str__(self):
        return str({"location": self.start, "text": self.text})


class FigureLocalizer(Localizer):

    def __init__(self, no):
        self.no  = no

    @staticmethod    
    def fromJSON(jsonString):
        return FigureLocalizer(jsonString["no"])

    def toJSON(self):
        return {"type":"figure", "no": self.no}

    def __str__(self):
        return str({"no": self.no})

class TableLocalizer(Localizer):

    def __init__(self, no, noRow=None, noCol=None):
        self.no      = no
        self.noRow     = noRow    
        self.noCol     = noCol    

    @staticmethod    
    def fromJSON(jsonString):
        if jsonString["noRow"] == "None":
            jsonString["noRow"] = None

        if jsonString["noCol"] == "None":
            jsonString["noCol"] = None

        return TableLocalizer(jsonString["no"], jsonString["noRow"], jsonString["noCol"])


    def toJSON(self):
        return {"type":"table", "no": self.no, "noRow":self.noRow, "noCol":self.noCol}


    def __str__(self):
        return str({"no": self.no, "noRow":self.noRow, "noCol":self.noCol})



class EquationLocalizer(Localizer):

    def __init__(self, no, equation=None):
        self.no          = no
        self.equation     = equation    

    @staticmethod    
    def fromJSON(jsonString):
        if jsonString["equation"] == "None":
            jsonString["equation"] = None

        return EquationLocalizer(jsonString["no"], jsonString["equation"])

    def toJSON(self):
        return {"type":"equation", "no": self.no, "equation":self.equation}


    def __str__(self):
        return str({"no": self.no, "equation":self.equation})




class PositionLocalizer(Localizer):

    def __init__(self, noPage, x, y, width, height):
        self.noPage = noPage
        self.x         = x
        self.y         = y
        self.width     = width
        self.height = height    


    @staticmethod    
    def fromJSON(jsonString):
        return PositionLocalizer(jsonString["noPage"], jsonString["x"], jsonString["y"], 
                                 jsonString["width"], jsonString["height"])

    def toJSON(self):
        return {"type":"position", "noPage": self.noPage, "x":self.x, "y":self.y, "width":self.width, "height":self.height}


    def __str__(self):
        return str({"noPage": self.noPage, "x":self.x, "y":self.y, "width":self.width, "height":self.height})





class Annotation:

    def __init__(self, comment = "", users=[], pubId="", localizer=None, experimentProperties=[]):
        if not isinstance(experimentProperties, list):
            raise ValueError        
        for expProp in experimentProperties:
            if not isinstance(expProp, ParamRef):
                raise ValueError        
        
        
        self.comment                = comment
        self.ID                     = str(uuid1())
        self.pubId                  = pubId
        self.users                  = users
        self.parameters             = []
        self.tags                   = []
        self.localizer              = localizer
        self.experimentProperties   = experimentProperties


    @property
    def tags(self):
        return self.__tags

    @tags.setter
    def tags(self, tags):
        if not isinstance(tags, list):
            raise TypeError
        for tag in tags:
            if not isinstance(tag, Tag):
                raise TypeError            
        self.__tags = tags


    @staticmethod    
    def readIn(fileObject):
        returnedAnnots = []
        try:
            jsonAnnots = json.load(fileObject)
        except ValueError:
            if fileObject.read() == "":
                return []
            else:
                print("File content: ", fileObject.read())
                raise

        for jsonAnnot in jsonAnnots:
            if jsonAnnot["version"] == "1":
                annot            = Annotation()
                annot.pubId      = jsonAnnot["pubId"]
                annot.ID         = jsonAnnot["annotId"]
                annot.comment    = jsonAnnot["comment"]
                annot.users      = jsonAnnot["authors"]
                annot.parameters = ParameterInstance.fromJSON(jsonAnnot["parameters"])
                
                # For backward compatibility
                if isinstance(jsonAnnot["tags"], dict):
                    annot.tags = [Tag(id, name) for id, name in jsonAnnot["tags"].items()]
                else:
                    annot.tags = [Tag.fromJSON(tag) for tag in jsonAnnot["tags"]]   
                
                
                if "experimentProperties" in jsonAnnot:
                    annot.experimentProperties = [ParamRef.fromJSON(prop) for prop in jsonAnnot["experimentProperties"]]
                else:
                    annot.experimentProperties = []
                if jsonAnnot["localizer"]["type"] == "text":
                    annot.localizer  = TextLocalizer.fromJSON(jsonAnnot["localizer"])
                elif jsonAnnot["localizer"]["type"] == "figure":
                    annot.localizer  = FigureLocalizer.fromJSON(jsonAnnot["localizer"])
                elif jsonAnnot["localizer"]["type"] == "table":
                    annot.localizer  = TableLocalizer.fromJSON(jsonAnnot["localizer"])
                elif jsonAnnot["localizer"]["type"] == "equation":
                    annot.localizer  = EquationLocalizer.fromJSON(jsonAnnot["localizer"])
                elif jsonAnnot["localizer"]["type"] == "position":
                    annot.localizer  = PositionLocalizer.fromJSON(jsonAnnot["localizer"])

                returnedAnnots.append(annot)
            else:
                raise ValueError("Format version not supported.")

        return returnedAnnots


    @property
    def type(self):
        if isinstance(self.localizer, TextLocalizer):
            return "text"
        elif isinstance(self.localizer, FigureLocalizer):
            return "figure"
        elif isinstance(self.localizer, TableLocalizer):
            return "table"
        elif isinstance(self.localizer, EquationLocalizer):
            return "equation"
        elif isinstance(self.localizer, PositionLocalizer):
            return "position"        


    @staticmethod    
    def dump(fileObject, annots):

        jsonAnnots = []
        for annot in annots:
            # Build and append the annotation...
            jsonAnnots.append(annot.toJSON())



        json.dump(jsonAnnots, fileObject, sort_keys=True, indent=4, separators=(',', ': '))


    def toJSON(self):
        return {"pubId":self.pubId, "annotId": self.ID, "version": "1", 
               "tags":[tag.toJSON() for tag in self.tags], "comment":self.comment, 
               "authors":self.users, "parameters":[param.toJSON() for param in self.parameters], 
               "localizer":self.localizer.toJSON(),
               "experimentProperties":[prop.toJSON() for prop in self.experimentProperties]}



    @property
    def text(self):
        if isinstance(self.localizer, TextLocalizer):
            return self.localizer.text
        elif isinstance(self.localizer, FigureLocalizer):
            return "Figure " + str(self.localizer.no) 
        elif isinstance(self.localizer, TableLocalizer):
            return "Table " + str(self.localizer.no)
        elif isinstance(self.localizer, EquationLocalizer):
            return "Equation " + str(self.localizer.no)
        elif isinstance(self.localizer, PositionLocalizer):
            return "Bounding box position"        
        else:
            raise AttributeError("Localizer type unknown: ", str(type(self.localizer)))

    @text.setter
    def text(self, text):
        if isinstance(self.localizer, TextLocalizer):
            self.localizer.text = text.encode("ascii", 'backslashreplace').decode("ascii").replace("\n", "\\n")
        else:
            raise AttributeError


    def getContext(self, contextLength=100, dbPath="./curator_DB", restServerURL=None):
        
        if not isinstance(self.localizer, TextLocalizer):
            return ""        

        try:
            txtFileName = join(dbPath, utils.Id2FileName(self.pubId)) + ".txt"
            
            if isfile(txtFileName):
                # Context is fetch locally
                with open(txtFileName, 'r', encoding="utf-8", errors='ignore') as f :
                    fileText = f.read()
                    contextStart = max(0, self.localizer.start - contextLength)
                    contextEnd = min(self.localizer.start + len(self.localizer.text) + contextLength, len(fileText))
                    return fileText[contextStart:contextEnd]
                    
            else:
                # Context is fetch through the RESTful server
                if restServerURL is None:
                    raise IOError("The context cannot be determined. The text " +
                                  "is not available in the local database and " +
                                  "no RESTful server URL has been provided to " +
                                  "fetch it remotely.")
                
                restClient = RESTClient(restServerURL)
                return restClient.getContext(self.pubId, contextLength,
                                             self.localizer.start, self.localizer.text)    

        except FileNotFoundError:
            print("File not found.")
            return ""




    @property
    def start(self):
        if isinstance(self.localizer, TextLocalizer):
            return self.localizer.start
        else:
            raise AttributeError

    @start.setter
    def start(self, start):
        if isinstance(self.localizer, TextLocalizer):
            self.localizer.start = start
        else:
            raise AttributeError



    @property
    def tagIds(self):
        return [tag.id for tag in self.tags]

    def addTag(self, id, name):
        self.tags.append(Tag(id, name))

    def removeTag(self, id):
        ids = self.tagIds
        
        del self.tags[ids.index(id)]

    def clearTags(self):
        self.tags = []


    def getSpecies(self):
        #TODO
        return None
        
    def getBrainRegion(self):
        #TODO
        return None
        
        

    @property
    def authors(self):
        return self.users
        
    @authors.setter
    def authors(self, authors):
        self.users = authors

    @property
    def paramTypeIds(self):
        return [param.typeID for param in self.parameters]    


    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return '"{}";"{}";"{}";"{}";{}'.format(self.ID, self.comment, type(TextLocalizer), self.users, self.tags)



class AnnotationListModel(QtCore.QAbstractTableModel):

    def __init__(self, parent, annotationList = [], header = ['ID', 'type', 'localizer', 'comment'], *args):
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.annotationList = annotationList
        self.header = header
        self.nbCol = len(header)
        self.sortCol   = 0 
        self.sortOrder = QtCore.Qt.AscendingOrder        

    def rowCount(self, parent=None):
        return len(self.annotationList)

    def columnCount(self, parent=None):
        return self.nbCol 


    def getSelectedAnnotation(self, selection):

        if isinstance(selection, list):
            if selection == []:
                return None
            elif isinstance(selection[0], QtCore.QModelIndex):
                index = selection[0]
        else:
            if selection.at(0) is None:
                return None
            index = selection.at(0).indexes()[0]
        return self.annotationList[index.row()]



    def getByIndex(self, annot, ind):
        if ind == 0:
            return annot.ID
        elif ind == 1:
            return str(annot.type)
        elif ind == 2:
            return str(annot.localizer)
        elif ind == 3 :
            return annot.comment
        else:
            raise ValueError

    def data(self, index, role):
        if not index.isValid():
            return None

        if role != QtCore.Qt.DisplayRole:
            return None

        return self.getByIndex(self.annotationList[index.row()], index.column())

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.header[col]
        return None

    def sort(self, col=None, order=None):
        if col is None:
            col = self.sortCol 
        if order is None:
            order = self.sortOrder

        """sort table by given column number col"""
        self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
        reverse = (order == QtCore.Qt.DescendingOrder)
        self.annotationList = sorted(self.annotationList, key=lambda x: self.getByIndex(x, col), reverse = reverse) #operator.itemgetter(col))
        #if order == QtCore.Qt.DescendingOrder:
        #    self.mylist.reverse()
        self.emit(QtCore.SIGNAL("layoutChanged()"))

    def refresh(self):
        self.emit(QtCore.SIGNAL("layoutChanged()"))


