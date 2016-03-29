#!/usr/bin/python3

__author__ = 'oreilly'
__email__  = 'christian.oreilly@epfl.ch'



#### Dictionnary to translate Neurolex ids used previously to their new 
#### KnowledgeSpace corresponding ids
nlx2ks = {"birnlex_254":"NIFORG:birnlex_254",
          "nifext_41":"NIFCELL:nifext_41",
          "birnlex_845":"NIFGA:birnlex_845",
          "birnlex_167":"NIFORG:birnlex_167",
          "birnlex_2300":"NIFINV:birnlex_2300",
          "nifext_8056":"NIFMOL:nifext_8056",
          "nifext_8054":"NIFMOL:nifext_8054",
          "birnlex_1721":"NIFGA:birnlex_1721",
          "birnlex_1608":"NIFGA:birnlex_1608",
          'birnlex_1595':'NIFGA:birnlex_1595',
          'birnlex_2313':'NIFINV:birnlex_2313',
          'birnlex_954':'NIFGA:birnlex_954',
          'birnlex_12718':'NIFDYS:birnlex_12718',
          'birnlex_113':'NIFORG:birnlex_113',
          'sao1797800540':"NIFMOL:sao1797800540",
          'GO_0030431':"GO:0030431",
          'nlx_cell_20081203':'NIFCELL:nlx_cell_20081203',
          'birnlex_1116':'NIFGA:birnlex_1116',
          'nifext_46':'NIFCELL:nifext_46',
          'sao1211023249':'NIFSUB:sao1211023249',
          'birnlex_2304':'NIFINV:birnlex_2304',
          'birnlex_160':'NIFORG:birnlex_160',
          'birnlex_721':'NIFGA:birnlex_721',
          'birnlex_297':'NIFORG:birnlex_297',
          'PATO_0000051':'PATO:0000051',
          'birnlex_737':'NIFGA:birnlex_737',
          'nifext_45':'NIFCELL:nifext_45',
          'birnlex_2547':'NIFGA:birnlex_2547',
          'nifext_8055':'NIFMOL:nifext_8055',
          'sao1813327414':'NIFCELL:sao1813327414',
          'nlx_organ_109041':"NIFORG:birnlex_160",
          'PATO_0000146':'PATO:0000146',
          "sao1846985919":"NIFMOL:sao1797800540"}

class Tag:
    def __init__(self, id, name):
        if not isinstance(id, str):
            raise TypeError
        if not isinstance(name, str):
            raise TypeError


        self.id = nlx2ks[id] if id in nlx2ks else id
        #self.id = id
        
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

        self.rootId = rootId

    def __repr__(self):
        return str(self.toJSON())

    def __str__(self):
        return str(self.toJSON())

    def toJSON(self):
        return {"id":self.id, "name":self.name, "rootId":self.rootId}

    @staticmethod
    def fromJSON(jsonString):
        return RequiredTag(jsonString["id"], jsonString["name"], jsonString["rootId"])

