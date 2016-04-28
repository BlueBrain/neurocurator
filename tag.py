#!/usr/bin/python3

__author__ = 'oreilly'
__email__  = 'christian.oreilly@epfl.ch'

from tagUtilities import nlx2ks


import qtNeurolexTree 
class Tag:
    
    ## TODO: remove this line once tag ids have been corrected in all annotatiuons
    treeData, dicData    = qtNeurolexTree.loadTreeData()   
    invDicData = {val:(nlx2ks[key] if key in nlx2ks else key) for key, val in dicData.items()}
    invDicData['Thalamus geniculate nucleus (lateral) principal neuron'] = 'NIFCELL:nlx_cell_20081203'
    invDicData["Young rat"] = "nlx_151691"
    invDicData["Thalamus geniculate nucleus (lateral) interneuron"] = "NIFCELL:nifext_46"
    invDicData["Temperature"] = "PATO:0000146"
    invDicData["Sleep"] = "GO:0030431"
    invDicData['Burst firing pattern'] = "nlx_78803"
    invDicData['Cat'] = 'NIFORG:birnlex_113'
    invDicData['Thalamus reticular nucleus cell'] = 'NIFCELL:nifext_45'
    invDicData['Afferent'] = "NIFGA:nlx_anat_1010"
    invDicData['Morphology'] = 'PATO:0000051'
    ##    
    
    def __init__(self, id, name):
        if not isinstance(id, str):
            raise TypeError
        if not isinstance(name, str):
            raise TypeError

        id = nlx2ks[id] if id in nlx2ks else id
        
        ## TODO: remove this line once tag ids have been corrected in all annotatiuons   
        if not Tag.dicData[id] == name:
            try:
                print("Incompatibility between in " + str(id) + ":" + str(name) + ". Correcting to " + 
                      str(Tag.invDicData[name]) + ":" + str(Tag.dicData[Tag.invDicData[name]]))
                id = Tag.invDicData[name]
                name = Tag.dicData[id]
            except:
                # "Thalamus relay cell"
                raise                
                #treeData, Tag.dicData    = qtNeurolexTree.loadTreeData()   
                #Tag.invDicData = {val:key for key, val in Tag.dicData.items()}  
                #print("Incompatibility between in " + str(id) + ":" + str(name) + ". Correcting to " + 
                #      str(Tag.invDicData[name]) + ":" + str(name))
                #id = Tag.invDicData[name]                
        ##       
            
        self.id = id
        self.name = name


    def __repr__(self):
        return str(self.toJSON())

    def __str__(self):
        return str(self.toJSON())

    def toJSON(self):
        return {"id":self.id, "name":self.name}

    @staticmethod
    def fromJSON(jsonString):
        return Tag(jsonString["id"], jsonString["name"])


class RequiredTag(Tag):
    def __init__(self, id, name, rootId):

        super(RequiredTag, self).__init__(id, name)

        if not isinstance(rootId, str):
            raise TypeError

        if "||" in rootId:
            self.modifier, rootId = rootId.split("||")
            self.optional = "OPTIONAL" in self.modifier
        else:
            self.modifier = ""



        self.rootId = rootId

    def __repr__(self):
        return str(self.toJSON())

    def __str__(self):
        return str(self.toJSON())

    def toJSON(self):
        if self.modifier == "":
            rootId = self.rootId
        else:
            rootId = self.modifier + "||" + self.rootId
        return {"id":self.id, "name":self.name, "rootId":rootId}

    @staticmethod
    def fromJSON(jsonString):
        return RequiredTag(jsonString["id"], jsonString["name"], jsonString["rootId"])



