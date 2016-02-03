#!/usr/bin/python3

__author__ = "Christian O'Reilly"

# Contributed libraries imports
from PySide import QtGui, QtCore
from os.path import join
import re
import numpy as np


from uiUtilities import disableTextWidget, enableTextWidget
from areaSelector import PDFAreaSelector, loadImage
from modelingParameter import getParameterTypes, ParameterListModel, ParameterInstance, \
	getParameterTypeIDFromName, unitIsValid
from autocomplete import AutoCompleteEdit
from annotation import TextLocalizer, FigureLocalizer, TableLocalizer, \
	EquationLocalizer, PositionLocalizer, Annotation
from difflib import SequenceMatcher
from approximateMatchDlg import MatchDlg




class ParamModWgt(QtGui.QWidget):

	def __init__(self, parent):

		self.parent = parent
		super(ParamModWgt, self).__init__()

		self.parameterTypes = getParameterTypes()

		# Widgets		
		self.paramsEdit = AutoCompleteEdit(self)

		self.paramsEdit.setModel([paramType.name for paramType in self.parameterTypes])
		self.paramValueEdit		= QtGui.QLineEdit(self)
		self.paramUnitEdit		= QtGui.QLineEdit(self)
		self.paramDescription	= QtGui.QTextEdit(self)
		unitLabel			    = QtGui.QLabel()
		unitLabel.setOpenExternalLinks(True)
		unitLabel.setTextFormat(QtCore.Qt.RichText)
		unitLabel.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
		unitLabel.setText("Unit (<a href=\"docs/_build/html/units.html\">?</a>)")


		self.newParamBtn        = QtGui.QPushButton("New")
		self.deleteParamBtn     = QtGui.QPushButton("Delete")
		self.paramSaveAnnotBtn  = QtGui.QPushButton("Save") 
		buttonWidget = QtGui.QWidget(self)

		self.paramListTblWdg  	= QtGui.QTableView() 
		self.paramListModel 	= ParameterListModel(self)
		self.paramListTblWdg.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self.paramListTblWdg.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
		self.paramListTblWdg.setModel(self.paramListModel)
		

		# Signals
		self.paramsEdit.activated[str].connect(self.paramTypeChanged)
		selectionModel = self.paramListTblWdg.selectionModel()
		selectionModel.selectionChanged.connect(self.selectedParameterChanged)

		#self.attributeParameter.stateChanged.connect(self.refreshModelingParam)
		self.paramValueEdit.textChanged.connect(self.parent.setNeedSaving)
		self.paramUnitEdit.textChanged.connect(self.parent.setNeedSaving)
		self.newParamBtn.clicked.connect(self.newParameter)
		self.deleteParamBtn.clicked.connect(self.deleteParameter)
		self.paramSaveAnnotBtn.clicked.connect(self.saveParam)


		# Layout
		buttonLayout = QtGui.QHBoxLayout(buttonWidget)
		buttonLayout.addWidget(self.paramSaveAnnotBtn)
		buttonLayout.addWidget(self.deleteParamBtn)
		buttonLayout.addWidget(self.newParamBtn)
		grid 	= QtGui.QGridLayout(self)
		grid.addWidget(QtGui.QLabel("Parameter"), 0, 0)
		grid.addWidget(QtGui.QLabel("Value"),     0, 1)
		grid.addWidget(unitLabel,      			  0, 2)

		grid.addWidget(self.paramsEdit,     1, 0)
		grid.addWidget(self.paramValueEdit, 1, 1)
		grid.addWidget(self.paramUnitEdit,  1, 2)

		grid.addWidget(buttonWidget, 2, 0, 1, 3)
		grid.addWidget(self.paramDescription, 0, 3, 3, 1)

		grid.addWidget(self.paramListTblWdg, 3, 0, 1, 4)

		# Initial behavior
		self.paramValueEdit.setValidator(QtGui.QDoubleValidator())
		self.paramsEdit.setEnabled(False)
		self.paramValueEdit.setEnabled(False)
		self.paramUnitEdit.setEnabled(False)
		#self.paramDescription.setEnabled(False)
		self.newParamBtn.setEnabled(True)
		self.deleteParamBtn.setEnabled(False)
		self.paramSaveAnnotBtn.setEnabled(False)
		self.additionMode = False
		self.paramDescription.setReadOnly(True)


	def selectedParameterChanged(self, selected, deselected):
		if len(selected.indexes()) == 0:
			return
		if self.additionMode:
			msgBox = QtGui.QMessageBox(self)
			msgBox.setWindowTitle("Cancellation")
			msgBox.setText("Are you sure you want to cancel the addition of the new parameter being edited? If not, say no and then hit 'Save' to save this new parameter.")
			msgBox.setStandardButtons(QtGui.QMessageBox.No | QtGui.QMessageBox.Yes)
			msgBox.setDefaultButton(QtGui.QMessageBox.No)
			if msgBox.exec_() == QtGui.QMessageBox.Yes:
				self.additionMode = False
				self.loadRow()
			else:
				#self.paramListTblWdg.selectRow(-1)
				self.paramListTblWdg.clearSelection()
		else:
			self.loadRow()


	def paramTypeChanged(self, paramName):
		for paramType in self.parameterTypes:
			if paramType.name == paramName:
				self.paramDescription.setText(paramType.description)
				self.paramValueEdit.setFocus()
			


	def newParameter(self):
		self.additionMode = True

		self.paramsEdit.setEnabled(True)
		self.paramValueEdit.setEnabled(True)
		self.paramUnitEdit.setEnabled(True)
	
		self.newParamBtn.setEnabled(False)
		self.deleteParamBtn.setEnabled(False)
		self.paramSaveAnnotBtn.setEnabled(True)
		#self.paramListTblWdg.setEnabled(False)

		self.paramValueEdit.setText("")
		self.paramUnitEdit.setText("")
		self.paramsEdit.setCurrentIndex(-1)
		self.paramDescription.setText("")
		self.paramsEdit.setFocus()

		self.paramListTblWdg.clearSelection()





	def saveParam(self):

		error = None
		typeID = getParameterTypeIDFromName(self.paramsEdit.currentText())
		if typeID is None:
			error = "parameter type"
		
		param = ParameterInstance(typeID)
		try:
			value = float(self.paramValueEdit.text())
		except:
			error = "value"

		unit = self.paramUnitEdit.text()
		if not unitIsValid(unit):
			error = "unit"

		if error is None:
			param.setValue(value, unit)
			param.setAnnotation(self.parent.currentAnnotation.ID, self.parent.IdTxt.text())

			selectedRow = self.paramListTblWdg.selectionModel().currentIndex().row()
			# Even when there is no selection, selectedRow can take a zero value. This "if" 
			# controls for that.
			if len(self.paramListTblWdg.selectionModel().selectedRows()) == 0:
				selectedRow = -1

			if selectedRow >= 0:
				self.parent.currentAnnotation.parameters[selectedRow] = param
			else:
				self.parent.currentAnnotation.parameters.append(param)

			self.additionMode = False
			self.parent.saveAnnotation()			

			if selectedRow >= 0:
				self.loadModelingParameter(selectedRow)
			else:
				self.loadModelingParameter(len(self.parent.currentAnnotation.parameters)-1)				

		else:
			msgBox = QtGui.QMessageBox(self)
			msgBox.setWindowTitle("Invalid modeling parameter")
			msgBox.setText("To save this annotation with an associated modeling parameter, a valid value and unit must be entered. The " + error + " entered is not valid.")
			msgBox.exec_() 



	def deleteParameter(self):
		selectedRow = self.paramListTblWdg.selectionModel().currentIndex().row()
		del self.parent.currentAnnotation.parameters[selectedRow]
		self.parent.saveAnnotation()
		self.refreshModelingParameters()



	def refreshModelingParameters(self):
		selectedRow = self.paramListTblWdg.selectionModel().currentIndex().row()
		self.loadModelingParameter(selectedRow)


	def loadModelingParameter(self, row = None):

		if self.parent.currentAnnotation is None:
			self.paramListModel.parameterList = []
		else:
			self.paramListModel.parameterList = self.parent.currentAnnotation.parameters

			aRowIsSelected = not row is None
			if aRowIsSelected:
				if row < 0:
					self.paramListTblWdg.selectRow(self.paramListTblWdg.model().rowCount()-row)
				else:
					self.paramListTblWdg.selectRow(row)

			else:
				## No rows are selected
				self.paramListTblWdg.selectRow(-1)
		
			self.paramsEdit.setEnabled(aRowIsSelected)
			self.paramValueEdit.setEnabled(aRowIsSelected)
			self.paramUnitEdit.setEnabled(aRowIsSelected)
	
			self.newParamBtn.setEnabled(True)
			self.deleteParamBtn.setEnabled(aRowIsSelected)
			self.paramSaveAnnotBtn.setEnabled(aRowIsSelected)

		self.paramListModel.refresh()


	def loadRow(self):
		selectedRow = self.paramListTblWdg.selectionModel().currentIndex().row()
		currentParameter = self.parent.currentAnnotation.parameters[selectedRow]
		self.paramValueEdit.setText(str(currentParameter.value))
		self.paramUnitEdit.setText(currentParameter.unit)

		aRowIsSelected = True

		self.paramsEdit.setEnabled(aRowIsSelected)
		self.paramValueEdit.setEnabled(aRowIsSelected)
		self.paramUnitEdit.setEnabled(aRowIsSelected)
	
		self.newParamBtn.setEnabled(True)
		self.deleteParamBtn.setEnabled(aRowIsSelected)
		self.paramSaveAnnotBtn.setEnabled(aRowIsSelected)

		for i in range(self.paramsEdit.count()):
			if self.paramsEdit.itemText(i) == currentParameter.name:
				self.paramsEdit.setCurrentIndex(i)
				self.paramTypeChanged(currentParameter.name)
				break




















class EditAnnotWgt(QtGui.QWidget):

	def __init__(self, parent):

		self.parent = parent
		super(EditAnnotWgt, self).__init__()

		# Widgets
		self.annotationTypesCbo		= QtGui.QComboBox(self)
		self.newAnnotationBtn		= QtGui.QPushButton('New', self)
		self.deleteAnnotationBtn	= QtGui.QPushButton('Delete', self)
		self.saveAnnotationBtn		= QtGui.QPushButton('Save', self)
		self.commentEdt				= QtGui.QTextEdit('', self)
	

		self.editAnnotWgt = {"text"    : EditAnnotTextWgt(self), 
					         "figure"  : EditAnnotFigureWgt(self), 
					         "table"   : EditAnnotTableWgt(self), 
					         "equation": EditAnnotEquationWgt(self), 
						     "position": EditAnnotPositionWgt(self)}

		# We use the list to as a redundancy of the list of keys in annotTypesDict
		# because we want these to be ordered. 
		self.annotTypeLst 	= ["text", "figure", "table", "equation", "position"]

		self.annotationTypesCbo.addItems(self.annotTypeLst)

		self.editAnnotTabs = QtGui.QTabWidget(self)

		for annotType in self.annotTypeLst:
			self.editAnnotTabs.addTab(self.editAnnotWgt[annotType], annotType)



		# Layout
		self.editAnnotGroupBox = QtGui.QGroupBox()
		gridAddAnnotations = QtGui.QGridLayout(self.editAnnotGroupBox)
		gridAddAnnotations.addWidget(QtGui.QLabel('Annotation type', self), 2, 0)
		gridAddAnnotations.addWidget(self.annotationTypesCbo, 2, 1)
		gridAddAnnotations.addWidget(self.saveAnnotationBtn, 2, 2)
		gridAddAnnotations.addWidget(self.deleteAnnotationBtn, 2, 3)
		gridAddAnnotations.addWidget(self.newAnnotationBtn, 2, 4)

		gridAddAnnotations.addWidget(self.editAnnotTabs, 3, 0, 1, 5)

		gridAddAnnotations.addWidget(QtGui.QLabel('Comment', self), 4, 0)
		gridAddAnnotations.addWidget(self.commentEdt, 4, 1, 1, 4)
		self.setLayout(gridAddAnnotations)



		# Signals
		self.saveAnnotationBtn.clicked.connect(self.saveAnnotation)
		self.newAnnotationBtn.clicked.connect(self.newAnnotation)
		self.deleteAnnotationBtn.clicked.connect(self.parent.deleteAnnotation)
		self.commentEdt.textChanged.connect(self.annotationChanged)
		self.annotationTypesCbo.currentIndexChanged.connect(self.setCurrentTab)

		self.parent.selectedAnnotationChangedConfirmed.connect(self.annotationSelectionChanged)
		for wgt in self.editAnnotWgt.values():
			self.parent.selectedAnnotationChangedConfirmed.connect(wgt.annotationSelectionChanged)
		self.parent.annotationCleared.connect(self.clearAddAnnotation)
		self.parent.savingNeeded.connect(self.savingNeeded)


		# Initial behavior
		self.deleteAnnotationBtn.setDisabled(True)
		self.annotationTypesCbo.setCurrentIndex(0)
		self.setCurrentTab(0)
		self.annotationTypesCbo.setDisabled(True)



	def saveAnnotation(self):
		self.parent.saveAnnotation()
		self.annotationTypesCbo.setDisabled(True)

		


	def selectAnnotType(self, annotType):
		
		ind = [no for no, a in enumerate(self.annotTypeLst) if a == annotType]
		if len(ind) != 1:
			raise ValueError("Invalid annotation type string.")
		ind = ind[0]

		self.annotationTypesCbo.setCurrentIndex(ind)
		self.annotationTypesCbo.setEnabled(False)


	def setCurrentTab(self, ind):
		self.editAnnotTabs.setCurrentIndex(ind) 

		for no in range(len(self.annotTypeLst)):
			self.editAnnotTabs.setTabEnabled(no, no == ind)
	


	@QtCore.Slot(object)
	def clearAddAnnotation(self):
		self.commentEdt.setText("")
		for widget in self.editAnnotWgt.values():
			widget.clearAnnotation()

	@property
	def detectAnnotChange(self):
		return self.parent.detectAnnotChange


	def annotationTextChanged(self):
		if self.detectAnnotChange:
			self.parent.setNeedSaving()


	def annotationChanged(self):
		if self.detectAnnotChange:
			self.parent.setNeedSaving()


	@property
	def currentAnnotation(self):
		return self.parent.currentAnnotation




	@QtCore.Slot(object)
	def annotationSelectionChanged(self):
		#self.deleteAnnotationBtn.setEnabled(True)
		self.newAnnotationBtn.setEnabled(True)
		if not self.parent.currentAnnotation is None:
			self.commentEdt.setText(self.currentAnnotation.comment)
			enableTextWidget(self.commentEdt)
		else:
			self.commentEdt.setText("")
			disableTextWidget(self.commentEdt)			
		
		self.deleteAnnotationBtn.setDisabled(self.parent.currentAnnotation is None)

	def newAnnotation(self):
		if self.parent.newAnnotation() :
			self.newAnnotationBtn.setEnabled(False)
			self.deleteAnnotationBtn.setEnabled(False)
			#self.saveAnnotationBtn.setEnabled(False)
			#disableTextWidget(self.commentEdt)	
			self.annotationTypesCbo.setEnabled(True)
			self.clearAddAnnotation()
			for widget in self.editAnnotWgt.values():
				widget.newAnnotation()
			self.annotationTypesCbo.setDisabled(False)




	@QtCore.Slot(object, bool)
	def savingNeeded(self, needSaving):
		self.saveAnnotationBtn.setEnabled(needSaving)



	def updateCurrentAnnotation(self):

		self.currentAnnotation.comment = self.commentEdt.toPlainText()
		if not self.parent.username in self.currentAnnotation.users:
			self.currentAnnotation.users.append(self.parent.username)
		self.editAnnotWgt[self.annotationTypesCbo.currentText()].updateCurrentAnnotation()










class EditAnnotFigureWgt(QtGui.QWidget):

	def __init__(self, container):
		self.container = container
		super(EditAnnotFigureWgt, self).__init__()

		# Widgets
		self.noFigure				= QtGui.QLineEdit('', self)
	
		# Signals
		self.noFigure.textChanged.connect(self.container.annotationChanged)

		# Layout
		self.editAnnotGroupBox = QtGui.QGroupBox()
		gridAddAnnotations = QtGui.QGridLayout(self.editAnnotGroupBox)
		gridAddAnnotations.addWidget(QtGui.QLabel('Figure no.', self), 2, 0)
		gridAddAnnotations.addWidget(self.noFigure, 2, 1)

		self.setLayout(gridAddAnnotations)

		# Initial behavior
		self.editAnnotGroupBox.setDisabled(True)
		disableTextWidget(self.noFigure)



	@QtCore.Slot(object)
	def annotationSelectionChanged(self):
		if not self.container.currentAnnotation is None:
			enableTextWidget(self.noFigure)
			if self.container.currentAnnotation.type == "figure":
				self.noFigure.setText(self.container.currentAnnotation.localizer.no)
		else:
			disableTextWidget(self.noFigure)
			self.noFigure.setText("")


	def newAnnotation(self):
		enableTextWidget(self.noFigure)


	def clearAnnotation(self):
		self.noFigure.setText("")


	def updateCurrentAnnotation(self):
		self.container.currentAnnotation.localizer = FigureLocalizer(self.noFigure.text())





class EditAnnotEquationWgt(QtGui.QWidget):

	def __init__(self, container):
		self.container = container
		super(EditAnnotEquationWgt, self).__init__()


		# Widgets
		self.noEquation				= QtGui.QLineEdit('', self)
		self.pythonStringEdt		= QtGui.QTextEdit('', self)
	
		# Signals
		self.noEquation.textChanged.connect(self.container.annotationChanged)
		self.pythonStringEdt.textChanged.connect(self.container.annotationChanged)

		# Layout
		self.editAnnotGroupBox = QtGui.QGroupBox()
		gridAddAnnotations = QtGui.QGridLayout(self.editAnnotGroupBox)
		gridAddAnnotations.addWidget(QtGui.QLabel('Equation no.', self), 2, 0)
		gridAddAnnotations.addWidget(self.noEquation, 2, 1)

		gridAddAnnotations.addWidget(QtGui.QLabel('Python representation', self), 3, 0)
		gridAddAnnotations.addWidget(self.pythonStringEdt, 3, 1)
		gridAddAnnotations.addWidget(QtGui.QLabel('(optional)', self), 3, 2)

		self.setLayout(gridAddAnnotations)

		# Initial behavior
		self.editAnnotGroupBox.setDisabled(True)
		disableTextWidget(self.noEquation)
		disableTextWidget(self.pythonStringEdt)



	@QtCore.Slot(object)
	def annotationSelectionChanged(self):

		if not self.container.currentAnnotation is None:
			enableTextWidget(self.noEquation)
			enableTextWidget(self.pythonStringEdt)
			if self.container.currentAnnotation.type == "equation":
				self.noEquation.setText(self.container.currentAnnotation.localizer.no)
				self.pythonStringEdt.setText(self.container.currentAnnotation.localizer.equation)
		else:
			disableTextWidget(self.noEquation)
			disableTextWidget(self.pythonStringEdt)
			self.noEquation.setText("")
			self.pythonStringEdt.setText("")


	def newAnnotation(self):
		enableTextWidget(self.noEquation)
		enableTextWidget(self.pythonStringEdt)


	def clearAnnotation(self):
		self.noEquation.setText("")
		self.pythonStringEdt.setText("")


	def updateCurrentAnnotation(self):
		pythonString = self.pythonStringEdt.toPlainText() if self.pythonStringEdt.toPlainText() != "" else None
		self.container.currentAnnotation.localizer = EquationLocalizer(self.noEquation.text(), pythonString)








class EditAnnotTableWgt(QtGui.QWidget):

	def __init__(self, container):
		self.container = container
		super(EditAnnotTableWgt, self).__init__()


		# Widgets
		self.noTable				= QtGui.QLineEdit('', self)
		self.noRow					= QtGui.QLineEdit('', self)
		self.noCol					= QtGui.QLineEdit('', self)
	
		# Signals
		self.noTable.textChanged.connect(self.container.annotationChanged)

		# Layout
		self.editAnnotGroupBox = QtGui.QGroupBox()
		gridAddAnnotations = QtGui.QGridLayout(self.editAnnotGroupBox)
		gridAddAnnotations.addWidget(QtGui.QLabel('Table no.', self), 2, 0)
		gridAddAnnotations.addWidget(self.noTable, 2, 1)

		gridAddAnnotations.addWidget(QtGui.QLabel('Row no.', self), 3, 0)
		gridAddAnnotations.addWidget(self.noRow, 3, 1)
		gridAddAnnotations.addWidget(QtGui.QLabel('(optional)', self), 3, 2)

		gridAddAnnotations.addWidget(QtGui.QLabel('Column no.', self), 4, 0)
		gridAddAnnotations.addWidget(self.noCol, 4, 1)
		gridAddAnnotations.addWidget(QtGui.QLabel('(optional)', self), 4, 2)

		self.setLayout(gridAddAnnotations)

		# Initial behavior
		self.editAnnotGroupBox.setDisabled(True)
		disableTextWidget(self.noTable)



	@QtCore.Slot(object)
	def annotationSelectionChanged(self):

		if not self.container.currentAnnotation is None:
			enableTextWidget(self.noTable)
			enableTextWidget(self.noRow)
			enableTextWidget(self.noCol)
			if self.container.currentAnnotation.type == "table":
				self.noTable.setText(self.container.currentAnnotation.localizer.no)
				self.noRow.setText(str(self.container.currentAnnotation.localizer.noRow))
				self.noCol.setText(str(self.container.currentAnnotation.localizer.noCol))
		else:
			disableTextWidget(self.noTable)
			disableTextWidget(self.noRow)
			disableTextWidget(self.noCol)
			self.noTable.setText("")
			self.noRow.setText("")
			self.noCol.setText("")


	def newAnnotation(self):
		enableTextWidget(self.noTable)
		enableTextWidget(self.noRow)
		enableTextWidget(self.noCol)
		#self.noTable.setFocus()

	def clearAnnotation(self):
		self.noTable.setText("")
		self.noRow.setText("")
		self.noCol.setText("")

	def updateCurrentAnnotation(self):
		noRow = self.noRow.text() if self.noRow.text() != "" else None
		noCol = self.noCol.text() if self.noCol.text() != "" else None
		self.container.currentAnnotation.localizer = TableLocalizer(self.noTable.text(), noRow, noCol)





class ImageThumbnail(QtGui.QLabel):

	def __init__(self, parent=None):
		super(ImageThumbnail, self).__init__(parent=parent)	

		self.setBackgroundRole(QtGui.QPalette.Base)
		self.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Sunken)
		#self.setScaledContents(True)

	#def resizeEvent(self, event):
	#	img = QtGui.QPixmap()
	#	w   = self.width()
	#	h   = self.height()
	#	self.setPixmap(self.pixmap().scaled(w, h, QtCore.Qt.KeepAspectRatio))






class EditAnnotPositionWgt(QtGui.QWidget):

	def __init__(self, container):
		self.container = container
		super(EditAnnotPositionWgt, self).__init__()


		# Widgets
		self.noPageTxt	 	= QtGui.QLineEdit('', self)
		self.xTxt		 	= QtGui.QLineEdit('', self)
		self.yTxt		 	= QtGui.QLineEdit('', self)
		self.widthTxt	 	= QtGui.QLineEdit('', self)
		self.heightTxt	 	= QtGui.QLineEdit('', self)
		self.imgThumbnail   = ImageThumbnail(self)
		self.selectAreaBtn 	= QtGui.QPushButton('Select area', self)

		# Signals
		self.noPageTxt.textChanged.connect(self.container.annotationChanged)
		self.selectAreaBtn.clicked.connect(self.selectArea)

		# Layout
		self.editAnnotGroupBox = QtGui.QGroupBox()
		gridAddAnnotations = QtGui.QGridLayout(self.editAnnotGroupBox)
		gridAddAnnotations.addWidget(QtGui.QLabel('Page no.', self), 2, 0)
		gridAddAnnotations.addWidget(self.noPageTxt, 2, 1)
		gridAddAnnotations.addWidget(QtGui.QLabel('x', self), 3, 0)
		gridAddAnnotations.addWidget(self.xTxt, 3, 1)
		gridAddAnnotations.addWidget(QtGui.QLabel('y', self), 4, 0)
		gridAddAnnotations.addWidget(self.yTxt, 4, 1)
		gridAddAnnotations.addWidget(QtGui.QLabel('width', self), 5, 0)
		gridAddAnnotations.addWidget(self.widthTxt, 5, 1)
		gridAddAnnotations.addWidget(QtGui.QLabel('height', self), 6, 0)
		gridAddAnnotations.addWidget(self.heightTxt, 6, 1)
		gridAddAnnotations.addWidget(self.selectAreaBtn, 7, 0, 1, 2)
		gridAddAnnotations.addWidget(self.imgThumbnail, 2, 2, 6, 1)


		gridAddAnnotations.setColumnStretch(0,1)
		gridAddAnnotations.setColumnStretch(1,1)
		gridAddAnnotations.setColumnStretch(2,3)

		self.setLayout(gridAddAnnotations)



		# Initial behavior
		self.editAnnotGroupBox.setDisabled(True)
		disableTextWidget(self.noPageTxt)
		disableTextWidget(self.xTxt)
		disableTextWidget(self.yTxt)
		disableTextWidget(self.widthTxt)
		disableTextWidget(self.heightTxt)



	@QtCore.Slot(object)
	def annotationSelectionChanged(self):

		if not self.container.currentAnnotation is None:
			if self.container.currentAnnotation.type == "position":
				self.noPageTxt.setText(str(self.container.currentAnnotation.localizer.noPage))
				self.xTxt.setText(str(self.container.currentAnnotation.localizer.x))
				self.yTxt.setText(str(self.container.currentAnnotation.localizer.y))
				self.widthTxt.setText(str(self.container.currentAnnotation.localizer.width))
				self.heightTxt.setText(str(self.container.currentAnnotation.localizer.height))
				self.loadThumbnail()
		else:
			self.noPageTxt.setText("")
			self.xTxt.setText("")
			self.yTxt.setText("")
			self.widthTxt.setText("")
			self.heightTxt.setText("")
			self.imgThumbnail.setPixmap(None)

	def newAnnotation(self):
		pass


	def clearAnnotation(self):
		self.noPageTxt.setText("")
		self.xTxt.setText("")
		self.yTxt.setText("")
		self.widthTxt.setText("")
		self.heightTxt.setText("")


	def updateCurrentAnnotation(self):
		self.container.currentAnnotation.localizer = PositionLocalizer(int(self.noPageTxt.text()), float(self.xTxt.text()), 
																	   float(self.yTxt.text()), float(self.widthTxt.text()), 
																	   float(self.heightTxt.text()))


	def selectArea(self):
		pdfFileName = join(self.container.parent.dbPath, self.container.parent.Id2FileName(self.container.parent.IdTxt.text())) + ".pdf"
		self.selectAreaDlg = PDFAreaSelector(pdfFileName)
		self.selectAreaDlg.areaSelected.connect(self.updateSelectedArea)
		self.selectAreaDlg.exec_()


	@QtCore.Slot()
	def updateSelectedArea(self):
		self.noPageTxt.setText(str(self.selectAreaDlg.currentPageInd+1))
		self.xTxt.setText(str(self.selectAreaDlg.x))
		self.yTxt.setText(str(self.selectAreaDlg.y))
		self.widthTxt.setText(str(self.selectAreaDlg.width))
		self.heightTxt.setText(str(self.selectAreaDlg.height))

		w   = self.imgThumbnail.width()
		h   = self.imgThumbnail.height()
		self.imgThumbnail.setPixmap(self.selectAreaDlg.image.scaled(w, h, QtCore.Qt.KeepAspectRatio))

	def loadThumbnail(self):
		pdfFileName = join(self.container.parent.dbPath, self.container.parent.Id2FileName(self.container.parent.IdTxt.text())) + ".pdf"
		pixmap = loadImage(pdfFileName,
					      self.container.currentAnnotation.localizer.noPage,
						  self.container.currentAnnotation.localizer.x,
						  self.container.currentAnnotation.localizer.y,
						  self.container.currentAnnotation.localizer.width,
						  self.container.currentAnnotation.localizer.height)
		self.imgThumbnail.setPixmap(pixmap)




class EditAnnotTextWgt(QtGui.QWidget):

	def __init__(self, container):
		self.container = container
		super(EditAnnotTextWgt, self).__init__()


		# Widgets
		self.localizeBtn		= QtGui.QPushButton('Localize', self)
		self.textToAnnotateTxt	= QtGui.QLineEdit('', self)
		self.contextTxt			= QtGui.QLineEdit('', self)
		self.startTxt			= QtGui.QLineEdit('', self)
	
		# Signals
		self.localizeBtn.clicked.connect(self.localizeText)
		self.textToAnnotateTxt.returnPressed.connect(self.localizeText)
		self.textToAnnotateTxt.textEdited.connect(self.setLocalizable)

		# Layout
		self.editAnnotGroupBox = QtGui.QGroupBox()
		gridAddAnnotations = QtGui.QGridLayout(self.editAnnotGroupBox)
		gridAddAnnotations.addWidget(QtGui.QLabel('Annotated text', self), 2, 0)
		gridAddAnnotations.addWidget(self.textToAnnotateTxt, 2, 1, 1, 2)
		gridAddAnnotations.addWidget(QtGui.QLabel('Context', self), 3, 0)
		gridAddAnnotations.addWidget(self.contextTxt, 3, 1, 1, 2)



		gridAddAnnotations.addWidget(QtGui.QLabel('Starting character', self), 4, 0)
		gridAddAnnotations.addWidget(self.startTxt, 4, 1)
		gridAddAnnotations.addWidget(self.localizeBtn, 4, 2)

		self.setLayout(gridAddAnnotations)

		# Initial behavior
		self.editAnnotGroupBox.setDisabled(True)
		disableTextWidget(self.textToAnnotateTxt)
		disableTextWidget(self.contextTxt)
		disableTextWidget(self.startTxt)
		self.localizeBtn.setDisabled(True)


	def localizeText(self):
		def recursiveSearch(queryString, text, a=0, level=0, maxLevel=5):

			starts = [(a, m.start(), len(queryString)) for m in re.finditer(re.escape(queryString), text)]
			if len(starts) == 0:
				if level < maxLevel and len(queryString) > 4:
					N = len(queryString)
					starts = []
					starts.extend(recursiveSearch(queryString[:int(N/2)], text, a, 			level+1, maxLevel))
					starts.extend(recursiveSearch(queryString[int(N/2):], text, a+int(N/2), level+1, maxLevel))
					return starts
				else:
					return starts
			else:
				return starts

		def processBlocks(blocks):
			for block in blocks:
				matcher = SequenceMatcher(None, queryStr, fileText[block["start"]:block["end"]])
				ratio = matcher.ratio()

				matcher.set_seq2(fileText[block["start"]-1:block["end"]])
				new_ratio = matcher.ratio()
				while new_ratio >= ratio and block["start"] > 0: 
					block["start"] -= 1
					ratio = new_ratio
					matcher.set_seq2(fileText[block["start"]-1:block["end"]])
					new_ratio = matcher.ratio()

				matcher.set_seq2(fileText[block["start"]+1:block["end"]])
				new_ratio = matcher.ratio()
				while new_ratio >= ratio and block["start"] < len(fileText)-1: 
					block["start"] += 1
					ratio = new_ratio
					matcher.set_seq2(fileText[block["start"]+1:block["end"]])
					new_ratio = matcher.ratio()

				matcher.set_seq2(fileText[block["start"]:block["end"]-1])
				new_ratio = matcher.ratio()
				while new_ratio >= ratio and block["end"] > 0: 
					block["end"] -= 1
					ratio = new_ratio
					matcher.set_seq2(fileText[block["start"]:block["end"]-1])
					new_ratio = matcher.ratio()

				matcher.set_seq2(fileText[block["start"]:block["end"]+1])
				new_ratio = matcher.ratio()
				while new_ratio >= ratio and block["end"] < len(fileText)-1: 
					block["end"] += 1
					ratio = new_ratio
					matcher.set_seq2(fileText[block["start"]:block["end"]+1])
					new_ratio = matcher.ratio()


				block["candidate"] 	= fileText[block["start"]:block["end"]]
				block["ratio"] 		= ratio
				block["candidate"] 	= block["candidate"].replace("\n", " ")		

			return np.array([block for block in blocks if block["ratio"] > 0.5])


		if len(self.textToAnnotateTxt.text()) < 3:
			errorMessage(self, "Error", "The text to localized should be at least 3-character long.")
			return			

		txtFileName = join(self.container.parent.dbPath, self.container.parent.Id2FileName(self.container.parent.IdTxt.text())) + ".txt"
	
		with open(txtFileName, 'r', encoding="utf-8", errors='ignore') as f :
			fileText = f.read()

		## We try to find an exact match...
		starts = [m.start() for m in re.finditer(re.escape(self.textToAnnotateTxt.text()), fileText)]

		## If now exact match was found...		
		if len(starts) == 0:

			## We try to find approximate matches using difflib
			queryStr = self.textToAnnotateTxt.text()
			N = len(self.textToAnnotateTxt.text())
			s = SequenceMatcher(None, queryStr, fileText)
			#matches = [match for match in s.get_matching_blocks()]	
			blocks = []
			#for match in matches:
			#	block				= {}
			#	block["start"]		= max(0, match.b-match.a)
			#	block["end"]		= min(block["start"]+N, len(fileText))
			#	blocks.append(block)
			#blocks = processBlocks(blocks)


			## No approximate match was found using difflib
			if len(blocks) == 0:

				## We try to find partial matches using a recursive algorithm that sequentially
				## splits the query string and try to find these subsetrings
				blocks = []
				for a, b, size in recursiveSearch(queryStr, fileText):
					block				= {}
					block["start"]		= max(0, b-a)
					block["end"]		= min(block["start"]+N, len(fileText))
					blocks.append(block)
				blocks = processBlocks(blocks)

			u, indices = np.unique([str(block["start"]) + "-" + str(block["end"]) for block in blocks], return_index=True)
			blocks = blocks[indices]
			blocks = sorted(blocks, key=lambda match: match["ratio"], reverse=True)
			matchDlg = MatchDlg(blocks, self.textToAnnotateTxt.text(), fileText, self)
			if matchDlg.exec_() == QtGui.QDialog.Accepted:
				starts = [matchDlg.chosenBlock["start"]]
			else:
				return

		elif len(starts) > 1:
			blocks = [{"start":m.start(), 
					   "end":m.start()+len(self.textToAnnotateTxt.text()), 
					   "candidate":self.textToAnnotateTxt.text()} for m in re.finditer(self.textToAnnotateTxt.text(), fileText)]
			matchDlg = MatchDlg(blocks, self.textToAnnotateTxt.text(), fileText, self)
			if matchDlg.exec_() == QtGui.QDialog.Accepted:
				starts = [matchDlg.chosenBlock["start"]]
			else:
				return
		
		contextStart = starts[0] - self.container.parent.contextLength
		contextEnd = starts[0] + len(self.textToAnnotateTxt.text()) + self.container.parent.contextLength
		self.contextTxt.setText(fileText[contextStart:contextEnd])
		
		localizer = TextLocalizer(self.textToAnnotateTxt.text(), starts[0])
		self.currentAnnotation = Annotation(self.container.commentEdt.toPlainText(), 
											[self.container.parent.username], 
											self.container.parent.IdTxt.text(), localizer)


		self.startTxt.setText(str(starts[0]))
		ID = self.container.parent.IdTxt.text()
		if ID in self.container.parent.selectedTagPersist:
			#self.currentAnnotation.clearTags()
			for tagId in self.container.parent.selectedTagPersist[ID]:
				self.container.currentAnnotation.addTag(tagId, self.container.parent.dicData[tagId])

		self.localizeBtn.setDisabled(True)
		disableTextWidget(self.textToAnnotateTxt)
		enableTextWidget(self.container.commentEdt)
		self.container.parent.tagAnnotGroupBox.setDisabled(False)
		self.container.parent.refreshTagList()		
		self.container.newAnnotationBtn.setEnabled(True)
		self.container.commentEdt.setFocus()
		self.container.parent.detectAnnotChange = True
		self.container.parent.needSaving = True



	@QtCore.Slot(object)
	def clearAnnotation(self):
		self.textToAnnotateTxt.setText("")
		self.contextTxt.setText("")
		self.startTxt.setText("")


	@QtCore.Slot(object)
	def annotationSelectionChanged(self):

		if not self.container.currentAnnotation is None:
			if self.container.currentAnnotation.type == "text":
				self.textToAnnotateTxt.setText(self.container.currentAnnotation.text)
				self.contextTxt.setText(self.container.parent.getCurrentContext())	
				self.startTxt.setText(str(self.container.currentAnnotation.start))	
				self.localizeBtn.setEnabled(False)
				disableTextWidget(self.textToAnnotateTxt)
		else:
			self.textToAnnotateTxt.setText("")
			self.contextTxt.setText("")	
			self.startTxt.setText("")	

	def setLocalizable(self):
		self.localizeBtn.setDisabled(len(self.textToAnnotateTxt.text()) < 3)


	def newAnnotation(self):
		enableTextWidget(self.textToAnnotateTxt)
		#self.textToAnnotateTxt.setFocus()



	def updateCurrentAnnotation(self):
		try:
			self.container.currentAnnotation.localizer = TextLocalizer(self.textToAnnotateTxt.text(), int(self.startTxt.text()))
		except ValueError:
			msgBox = QtGui.QMessageBox(self)
			msgBox.setWindowTitle("Invalide localizer")
			msgBox.setText("Before saving changes to this annotation, you must enter and \"Annotated text\" and then localize it.")
			msgBox.setStandardButtons(QtGui.QMessageBox.Ok)
			msgBox.exec_()


