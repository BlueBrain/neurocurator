#!/usr/bin/python3

__author__ = "Christian O'Reilly"

import urllib
from bs4 import BeautifulSoup


def checkID(ID): 
	if "PMID" in ID:
		return checkPMID(ID)
	else:
		return checkDOI(ID)


def checkPMID(ID):
	idKind, PMID = ID.split("_")
	url = "http://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?tool=curator&email=christian.oreilly@epfl.ch&ids=" + PMID + "&format=json&versions=no"
	try:
		with urllib.request.urlopen(url) as response:
		   html = response.read()
	except urllib.error.HTTPError:
		return False

	soup = BeautifulSoup(html, "lxml")
	return eval(str(soup)[15:-19])["status"] == "ok"



def checkDOI(DOI):
	# Using the rest API: http://www.doi.org/factsheets/DOIProxy.html#rest-api


	# Replacement characters according to http://www.doi.org/factsheets/DOIProxy.html#rest-api
	# but "%" signs must be replaced first since they are involved in the other replaced characters.
	if '%' in DOI:
		DOI = DOI.replace('%', '%25')

	replacementDict = {'"':'%22', '#':'%23', ' ':'%20', '?':'%3F', 
		'<':'%3C', '>':'%3E', '{':'%7B', '}':'%7D', '^':'%5E', 
		'[':'%5B', ']':'%5D', '`':'%60', '|':'%7C', '\\':'%5C', '+':'%2B'}

	# When Zotero imports from pubmed, it uses the "&lt;" for "<" and "&gt;" for ">"
	# so we also replace these.
	replacementDict["&lt;"] = '%3C'
	replacementDict["&gt;"] = '%3E'

	for key, value in replacementDict.items():
		if key in DOI:
			DOI = DOI.replace(key, value)

	url = "http://doi.org/api/handles/" + DOI
	try:
		with urllib.request.urlopen(url) as response:
		   html = response.read()
	except urllib.error.HTTPError:
		return False

	soup = BeautifulSoup(html, "lxml")
	# For some reason the "soup" string sometime contrains 
	# dictionnary entries with values that are equare to 
	# 'true' instead of 'True' which cannot be processed
	# by the python's eval function.
	soup = str(soup)[15:-18].replace("true", "True")
	return eval(soup)["responseCode"] == 1




if __name__ == "__main__":
	print(checkPMID("PMID_3303249260")) # False
	print(checkPMID("PMID_3309260")) # True
	print(checkPMID("PMID_26601117")) # True
	print(checkPMID("PMID_26584868")) # True

