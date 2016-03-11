
import pickle
from copy import deepcopy
import numpy as np
import operator
from annotation import Annotation

class TagSuggester:

	def __init__(self):
		self.usedTag = {}
		self.globalVsLocalRatio = 0.5

	def addUsedTag(self, tagId):
		if tagId in self.usedTag:
			self.usedTag[tagId] += 1
		else:
			self.usedTag[tagId] = 1
		self.save()


	def removeUsedTag(self, tagId):
		if tagId in self.usedTag:
			self.usedTag[tagId] -= 1
			self.save()



	def suggestions(self, annotationFileName, selectedIds, numberOfSuggestions=30):
		if len(self.usedTag) == 0:
			return []

		tagScores = deepcopy(self.usedTag)
		
		# Computing global indice
		maxGlobalUse = np.max(list(tagScores.values())) / self.globalVsLocalRatio

		# To avoid zero division
		if maxGlobalUse == 0:
			maxGlobalUse = 1.0 / self.globalVsLocalRatio

		for key in tagScores:
			tagScores[key] /= maxGlobalUse 



		# Computing local indices
		localScores = {}
		try :
			with open(annotationFileName, 'r', encoding="utf-8", errors='ignore') as f:		
				annots = Annotation.readIn(f)
				for annot in annots:
					for tagId in annot.tags:
						if tagId in localScores:
							localScores[tagId] += 1
						else:
							localScores[tagId] = 1
		except FileNotFoundError:
			pass
		
		if len(localScores):
			maxLocallUse = np.max(list(localScores.values())) / (1.0 - self.globalVsLocalRatio)
			for key in localScores:
				if not key in tagScores:
					tagScores[key]  = localScores[key] / maxLocallUse
				else:
					tagScores[key] += localScores[key] / maxLocallUse


		for key in selectedIds:
			if key in tagScores:
				del tagScores[key]


		if len(tagScores):
			keys, values = zip(*sorted(tagScores.items(), key=operator.itemgetter(1) , reverse=True))
			return list(keys[:min(numberOfSuggestions, len(keys))])
		else:
			return []


	@staticmethod
	def load(fileName="suggester.pickle"):
		try:
			with open(fileName, 'rb') as f:
				return pickle.load(f)
		except:
			return TagSuggester()

	def save(self, fileName="suggester.pickle"):
		try:
			with open(fileName, 'wb') as f:
				pickle.dump(self, f)
		except:
			pass



	
