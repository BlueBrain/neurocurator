#!/usr/bin/python3

__author__ = 'oreilly'
__email__  = 'christian.oreilly@epfl.ch'


from glob import glob
from annotation import Annotation
from modelingParameter import NumericalVariable, getParameterTypeNameFromID, Variable
from qtNeurolexTree import flatten_list, loadTreeData, TreeData
import pandas as pd
import numpy as np

annotationKeys         = ["Annotation type", "Publication ID", "Has parameter", "Tag name", "Author"]
annotationResultFields = ["Annotation type", "Publication ID", "Nb. parameters", "Tag name", "Comment", "Authors", "Localizer"]

parameterKeys          = ["Parameter name", "Result type", "Unit", "Required tag name", "Annotation ID", "Publication ID", "Tag name"]
parameterResultFields  = ["Required tag names", "Result type", "Values", "Parameter name", 
                          "Parameter type ID", "Parameter instance ID", "Unit", "Text", "Context"] 


class Condition:

    def apply_param(self, parameters):
        return parameters
        

    def apply_annot(self, annotations):
        return annotations
        





def checkAnnotation(annotation, key, value):

    if key == "Annotation type":
        return annotation.type == value  
        
    elif key == "Publication ID":        
        return annotation.pubId == value    
        
    elif key == "Has parameter":        
        return (len(annotation.parameters) > 0) == bool(value)   
        
    elif key == "Tag name":        
        print(value, annotation.tags)
        for tag in annotation.tags:
            if tag.name == value:
                return True
        return False        
        
    elif key == "Author":        
        for author in annotation.authors:
            if author == value:
                return True
        return False        
        
    else:
        raise ValueError("Parameter key '" + str(key) + "' is not available for search.")







def checkParameter(parameter, annotation, key, value):

    if key == "Parameter name":
        return getParameterTypeNameFromID(parameter.description.depVar.typeId) == value  
        
    elif key == "Result type":        
        return parameter.description.type == value        
        
    elif key == "Unit":
        if isinstance(parameter.description.depVar, Variable):
            return parameter.description.depVar.unit == value
        elif isinstance(parameter.description.depVar, NumericalVariable):
            return parameter.description.depVar.values.textUnit() == value
        else:
            raise TypeError
            
    elif key == "Required tag name":
        for tag in parameter.requiredTags:
            if tag.name == value:
                return True
        return False
        
    elif key == "Annotation ID":
        return annotation.annotId == value        

        
    elif key == "Publication ID":
        return annotation.pubId == value      
        
    elif key == "Tag name":
        for tag in annotation.tags:
            if tag.name == value:
                return True
        return False
        
    elif key == "Keyword":        
        raise NotImplemented
    else:
        raise ValueError("Parameter key '" + str(key) + "' is not available for search.")



class ConditionAtom(Condition):
    def __init__(self, key, value):
        if not isinstance(key, str):
            raise TypeError
        if not isinstance(value, str):
            raise TypeError
            
        self.key   = key
        self.value = value

    def apply_param(self, parameters):
        return {param:annot for param, annot in parameters.items() 
                            if checkParameter(param, annot, self.key, self.value)}
        
    def apply_annot(self, annotations):
        return {annot for annot in annotations 
                            if checkAnnotation(annot, self.key, self.value)}


class ConditionAND(Condition):

    def __init__(self, conditions):
        if not isinstance(conditions, list):
            raise TypeError
        for condition in conditions:
            if not isinstance(condition, Condition):
                raise TypeError
        self.conditions = conditions

    def apply_param(self, parameters):
        for condition in self.conditions:
            parameters = condition.apply_param(parameters)
        return parameters      
        
        
        
    def apply_annot(self, annotations):
        for condition in self.conditions:
            annotations = condition.apply_annot(annotations)
        return annotations      
        
            
    
class ConditionOR(Condition):
    
    def __init__(self, conditions):
        if not isinstance(conditions, list):
            raise TypeError
        for condition in conditions:
            if not isinstance(condition, Condition):
                raise TypeError
        self.conditions = conditions

    def apply_param(self, parameters):
        paramOut = {}
        for condition in self.conditions:
            parameters = condition.apply_param(parameters)
            paramOut.update(parameters)
        return paramOut              
        
        
    def apply_annot(self, annotations):
        annotOut = []
        for condition in self.conditions:
            annotations = condition.apply_annot(annotations)
            for annot in annotations:
                if not annot in annotOut:
                    annotOut.append(annot)
        return annotOut       
                
        
class ConditionNOT(Condition):

    def __init__(self, condition):
        if not isinstance(condition, Condition):
            raise TypeError
        self.condition = condition


    def apply_param(self, parameters):
        paramToRemove = self.condition.apply_param(parameters)
        for key in paramToRemove:
            del parameters[key]
        return parameters        
        
        
    def apply_annot(self, annotations):
        annotToRemove = self.condition.apply_annot(annotations)
        for annot in annotToRemove:
            annotations.remove(annot)
        return annotations      
                


class Search:
    
    def __init__(self, pathDB='./curator_DB'):
        self.treeData, self.dicData    = loadTreeData()
        self.conditions = Condition()    
        
        self.pathDB     = pathDB 
        self.getAllAnnotations()
        self.selectedItems = None

    def searchAnnotations(self):
        pass

    def searchParameters(self):
        pass

    
    def setSearchConditions(self, conditions):
        if not isinstance(conditions, Condition):
            raise TypeError            
        self.conditions = conditions

    
    def setResultFields(self, resultFields):
        self.resultFields = resultFields
    


    def getAllAnnotations(self):
        self.annotations = []
        for fileName in glob(self.pathDB + "/*.pcr"):
            #try:
            self.annotations.extend(Annotation.readIn(open(fileName, "r", encoding="utf-8", errors='ignore')))
            #except:       
            #    print("Skipping: ", fileName)    
            #    raise
            


class AnnotationSearch(Search):
    
    def __init__(self, pathDB='./curator_DB'):
        super(AnnotationSearch, self).__init__(pathDB)
        self.resultFields = annotationResultFields

    def search(self):
        self.selectedItems = self.conditions.apply_annot(self.annotations)
        resultDF           = self.formatOutput(self.selectedItems)
        return resultDF


    def formatOutput(self, annotations):

        results = {"obj_annotation":annotations} 
        for field in self.resultFields:
            
            if field == "Annotation type":
                results[field] = [annot.type for annot in annotations]                

            elif field == "Publication ID":
                results[field] = [annot.pubId for annot in annotations]                    
                                 
            elif field == "Nb. parameters":
                results[field] = [len(annot.parameters) for annot in annotations]          
                                 
            elif field == "Comment":
                results[field] = [annot.comment for annot in annotations]  
                
            elif field == "Authors":
                results[field] = [annot.authors for annot in annotations]          

            elif field == "Localizer":
                results[field] = [annot.text for annot in annotations]          

            elif field == "Tag name":
                try:
                    results[field] = [[tag.name for tag in annot.tags] for annot in annotations]         
                except AttributeError:
                    for annot in annotations:
                        print(annot.tags)
                    raise
             
            else :
                raise ValueError

        return pd.DataFrame(results)





class ParameterSearch(Search):
    
    def __init__(self, pathDB='./curator_DB'):
        super(ParameterSearch, self).__init__(pathDB)
        self.resultFields = parameterResultFields
        self.getAllParameters()
        self.expandRequiredTags = False
        self.onlyCentralTendancy = False    


    def search(self):
        self.selectedItems = self.conditions.apply_param(self.parameters)
        resultDF           = self.formatOutput(self.selectedItems)
        return resultDF


    def formatOutput(self, parameters):

        results = {"obj_parameter":list(parameters.keys()), "obj_annotation":list(parameters.values())}
        annotations = list(parameters.values())
        
        
        for field in self.resultFields:
            
            if field == "Parameter name":
                results[field] = [getParameterTypeNameFromID(param.description.depVar.typeId) for param in parameters]                
            
            elif field == "Text":
                results[field] = [annot.text for annot in annotations]                
            
            elif field == "Context":
                results[field] = [annot.getContext() for annot in annotations]                

            elif field == "Result type":
                results[field] = [param.description.type for param in parameters]               
                        
            elif field == "Required tag names":
                if self.expandRequiredTags:
                    tagCats = np.unique(flatten_list([[tag.rootId for tag in param.requiredTags] 
                                                                  if len(param.requiredTags) 
                                                                  else "" 
                                                                  for param in parameters]))
                    for tagCatId in tagCats:
                        tagNames = []
                        for param in parameters:
                            tagName = ""
                            for tag in param.requiredTags:
                                if tag.rootId == tagCatId:
                                    tagName = tag.name
                                    break
                            tagNames.append(tagName)
                                
                        results[self.dicData[tagCatId]] = tagNames

                else:
                     results[field] = [[tag.name for tag in param.requiredTags] 
                                                 if len(param.requiredTags) 
                                                 else "" 
                                                 for param in parameters]

       
            elif field == "Parameter type ID":
                results[field] = [param.description.depVar.typeId for param in parameters]            
             
            elif field == "Parameter instance ID":
                results[field] = [param.id for param in parameters]            


            elif field == "Unit":
                units = []
                for param in parameters:
                    if isinstance(param.description.depVar, Variable):
                        units.append(param.description.depVar.unit)
                    elif isinstance(param.description.depVar, NumericalVariable):
                        units.append(param.description.depVar.values.textUnit())
                    else:
                        raise TypeError
                results[field] = units



            elif field == "Values":
                if self.onlyCentralTendancy:
                    results[field] =  [param.description.depVar.values.centralTendancy() 
                                        if isinstance(param.description.depVar, NumericalVariable)
                                        else np.nan 
                                        for param in parameters]                                            
                else:
                    results[field] =  [param.description.depVar.values.text() 
                                        if isinstance(param.description.depVar, NumericalVariable)
                                        else np.nan 
                                        for param in parameters]            
            else :
                raise ValueError

        return pd.DataFrame(results)



    def getAllParameters(self):
        self.parameters = flatten_list([[(param, annot) for param in annot.parameters] for annot in self.annotations])
        self.parameters = {param:annot for param, annot in self.parameters}
        




if __name__ == "__main__":

    searcher = ParameterSearch()
    searcher.setSearchConditions(ConditionAtom("Parameter name", "conductance_ion_curr_max"))
    searcher.expandRequiredTags = True

    result = searcher.search()
    print(result)