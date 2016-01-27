#!/usr/bin/python3

__author__ = "Christian O'Reilly"

import urllib
from bs4 import BeautifulSoup

def checkDOI(DOI):
	url = "http://dx.doi.org/" + DOI
	try:
		with urllib.request.urlopen(url) as response:
		   html = response.read()
	except urllib.error.HTTPError:
		return False

	soup = BeautifulSoup(html, "lxml")
	return not "DOI Not Found" in soup.title.string

