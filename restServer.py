#!flask/bin/python
# -*- coding: utf-8 -*-
"""
Created on Sun Jun  5 14:50:40 2016

@author: oreilly
"""


from flask import Flask, jsonify, abort, make_response, request
import json, os
from subprocess import check_call
import difflib as dl

from os.path import join, isfile
dbPath = "/mnt/curator_DB/"

app = Flask(__name__)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

"""
@app.route('/neurocurator/api/v1.0/localize', methods=['POST'])
def localizeAnnotation():

    if not request.json        or
       not'id' in request.json or
       not 'annotStr' in request.json:
        abort(400)

    id       = request.json['id']
    annotStr = request.json['annotStr']


    return jsonify({'tasks': tasks})
	if ...:
		abort(404)
	return ...

"""


@app.route('/neurocurator/api/v1.0/localize', methods=['POST'])
def localizeAnnotation():
    if (not request.json         or
        not 'id' in request.json or
        not 'annotStr' in request.json):
        abort(400)

    id       = request.json['id']
    annotStr = request.json['annotStr']

    return jsonify({'test': "localize"})


@app.route('/neurocurator/api/v1.0/get_context', methods=['POST'])
def getContext():
    if (not request.json         or
        not 'id' in request.json or
        not 'annotStr' in request.json):
        abort(400)

    id       = request.json['id']
    annotStr = request.json['annotStr']

    return jsonify({'test': "get_context"})



@app.route('/neurocurator/api/v1.0/import_pdf', methods=['POST'])
def importPDF():
    if (not request.files       or
        not request.form        or
        not "file" in request.files or
        not "json" in request.form  or
        not 'paperId' in request.form["json"]):
        abort(400)


    paperId = json.loads(request.form["json"])["paperId"]
    pdf           = request.files["file"] #.read()


    if isPDFInDb(paperId):    
        similarity = isUserPDFValid(paperId, pdf)
        return str(similarity)
 
    #pdf           = request.files["file"] #.read()

    print(type(pdf))
    return jsonify({'paperId': paperId, "pdf":pdf})
    #return None








@app.route('/neurocurator/api/v1.0/check_similarity', methods=['POST'])
def checkSimilarity():
    if (not request.files	or
        not request.form        or
        not "file" in request.files or
        not "json" in request.form  or
        not 'paperId' in request.form["json"]):
        abort(400)

    paperId = json.loads(request.form["json"])["paperId"]
    pdf     = request.files["file"] #.read()


    if isPDFInDb(paperId):
        similarity = isUserPDFValid(paperId, pdf)
        return str(similarity)
    
    return None







@app.route('/neurocurator/api/v1.0/get_pdf', methods=['POST'])
def getServerPDF():
    if (not request.json         or
        not 'id' in request.json or
        not 'annotStr' in request.json):
        abort(400)

    id       = request.json['id']
    annotStr = request.json['annotStr']

    return jsonify({'test': "get_pdf"})


def runRESTServer():
    app.run(debug=True, host= '0.0.0.0')





def isPDFInDb(paperId):
    return isfile(join(dbPath, paperId) + ".pdf")

def isUserPDFValid(paperId, userPDF):
    if not isPDFInDb(paperId):
         return None

    userPDF.save("temp.pdf")
    # check_call is blocking
    check_call(['pdftotext', '-enc', 'UTF-8', "temp.pdf", "temp.txt"])
    os.remove("temp.pdf")
    
    ##### isSimilar = compare temp.txt to open(join(dbPath, paperId) + ".txt", 'r')

    """
    print("####1")
    a = open("temp.txt", 'r').read()
    b = open(join(dbPath, paperId) + ".txt", 'r').read()

    sim = dl.get_close_matches
    s = 0
    wa = a.split()
    wb = b.split()

    print("####2")
    for i in wa:
        if sim(i, wb):
            s += 1

    n = float(s) / float(len(wa))
    print('%d%% similarity' % int(n * 100))
    """


    a = open("temp.txt", 'r').read()
    b = open(join(dbPath, paperId) + ".txt", 'r').read()

    import nltk, string
    from sklearn.feature_extraction.text import TfidfVectorizer

    stemmer = nltk.stem.porter.PorterStemmer()
    remove_punctuation_map = dict((ord(char), None) for char in string.punctuation)

    def stem_tokens(tokens):
        return [stemmer.stem(item) for item in tokens]

    '''remove punctuation, lowercase, stem'''
    def normalize(text):
        return stem_tokens(nltk.word_tokenize(text.lower().translate(remove_punctuation_map)))

    vectorizer = TfidfVectorizer(tokenizer=normalize, stop_words='english')

    def cosine_sim(text1, text2):
        tfidf = vectorizer.fit_transform([text1, text2])
        return ((tfidf * tfidf.T).A)[0,1]

    similarity = cosine_sim(a, b)

    os.remove("temp.txt")

    #isSimilar = True
    #return isSimilar
    return similarity

    

def getDbTxt(paperId):
    return open(join(dbPath, paperId) + ".txt", 'r')


# copy this script at /usr/local/neurocurator and run with "curl -i bbpca063.epfl.ch:5000/neurocurator/api/v1.0/tasks"
