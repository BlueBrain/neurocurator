# -*- coding: utf-8 -*-
"""
Created on Sun Jun  5 13:08:43 2016

@author: oreilly
"""

import requests   
import json
import os

"""
            if os.path.isfile(saveFileName + ".txt"):
                errorMessage(self, "Error", "This PDF has already been imported to the database.")

            check_call(['pdftotext', '-enc', 'UTF-8', fileName.encode("utf-8").decode("utf-8"), saveFileName + ".txt"])
            copyfile(fileName, saveFileName + ".pdf")

            open(saveFileName + ".pcr", 'w', encoding="utf-8", errors='ignore')
            self.gitMng.addFiles([saveFileName + ".pcr", saveFileName + ".txt"])

            if gitPDF:
                self.gitMng.addFiles([saveFileName + ".pdf"])
                self.needPush = True

"""

class RESTClient:

    def __init__(self, serverURL):
        self.serverURL = serverURL


    def query(self):
        url = 'http://ES_search_demo.com/document/record/_search?pretty=true'
        data = '{"query":{"bool":{"must":[{"text":{"record.document":"SOME_JOURNAL"}},{"text":{"record.articleTitle":"farmers"}}],"must_not":[],"should":[]}},"from":0,"size":50,"sort":[],"facets":{}}'
        response = requests.get(url, data=data)
        return response
    
    def localizeAnnotation(self, paperId, textToAnnotate):
        pass
        # return blocks
    
    def getContext(self, paperId, contextLength, annotStart, annotText):
        pass
        # return contextString...
        
    def gotConnectivity(self):
        pass
        # return true/false
        
    def importPDF(self, localPDF, paperId):
        files = {"file": (os.path.basename(localPDF), open(localPDF, 'rb'), 'application/octet-stream'),
		 "json": (None, json.dumps({"paperId": paperId}), 'application/json')}
 
        response = requests.post(#"http://httpbin.org/post", 
                                 self.serverURL + "import_pdf", 
                                 files=files)
                                 
        return json.loads(response.content.decode("utf8"))





    #def removePDF(self, paperID):
    #    files = {"file": (os.path.basename(localPDF), open(localPDF, 'rb'), 'application/octet-stream'),
    #             "json": (None, json.dumps({"paperId": paperId}), 'application/json')}
    # 
    #    response = requests.post(#"http://httpbin.org/post",
    #                             self.serverURL + "check_similarity",
    #                             files=files)
    #    return response.content        




    def checkSimilarity(self, localPDF, paperId):
        files = {"file": (os.path.basename(localPDF), open(localPDF, 'rb'), 'application/octet-stream'),
                 "json": (None, json.dumps({"paperId": paperId}), 'application/json')}
 
        response = requests.post(#"http://httpbin.org/post",
                                 self.serverURL + "check_similarity",
                                 files=files)
        return response.content



        
    def getServerPDF(self, paperId):
        pass
        # return pdfFile



from glob import glob
def checkSimilarities(dbPath):
    client = RESTClient("http://bbpca063.epfl.ch:5000/neurocurator/api/v1.0/")

    intra = []
    inter = []
    for f1 in glob(os.path.join(dbPath, "*.pdf")):
        for f2 in glob(os.path.join(dbPath, "*.pdf")):
            try:
                print(f1, f2)
                response = client.checkSimilarity(f1, os.path.basename(f2)[:-4])
                if f1 == f2:
                    intra.append(float(response))
                else:
                    inter.append(float(response))
            except ValueError:
                pass

    return intra, inter




def checkImportPDF(localPDF, paperId):
    client = RESTClient("http://bbpca063.epfl.ch:5000/neurocurator/api/v1.0/")
    response = json.loads(client.importPDF(localPDF, paperId).decode("utf8"))
    #client.removePDF(localPDF)
    return response

if __name__ == "__main__":
    from qtNeurolexTree import TreeData
    from utils import Id2FileName    
    
    #checkSimilarities("/mnt/curator_DB/")
    paperId  = Id2FileName("10.3389/fncel.2016.00168")
    localPDF = "test.pdf" 
    response = checkImportPDF(localPDF, paperId)
    print(response)
    if response["status"] == "success":
        with open("test.txt", "w", encoding="utf8") as f:
            f.write(response["textFile"])
    else:
        raise ValueError(response["message"])        
    