#!/usr/bin/python3

__author__ = "Christian O'Reilly"

# Contributed libraries imports
from PySide import QtGui


from nat.modelingParameter import Relationship
from nat.tag import Tag


class ParamRelationWgt(QtGui.QWidget):

    def __init__(self, parent):
        super(ParamRelationWgt, self).__init__()

        self.parent = parent


        # Widgets        
        self.relationshipCbo    = QtGui.QComboBox(self)
        self.relationshipCbo.addItems(["unspecified", "point", "directed", "undirected"])

        self.relationStack        = QtGui.QStackedWidget(self)

        self.relationWgt   = QtGui.QWidget()
        self.relEntity1Cbo = QtGui.QComboBox(self.relationWgt)
        self.relEntity2Cbo = QtGui.QComboBox(self.relationWgt)
        self.relEntity1Lbl = QtGui.QLabel("Entity 1")
        self.relEntity2Lbl = QtGui.QLabel("Entity 2")
        self.infoLabel     = QtGui.QLabel("Note: Entity comboboxes are populated from selected tags.")

        relationLayout = QtGui.QGridLayout(self.relationWgt)
        relationLayout.addWidget(self.relEntity1Lbl, 0, 0)
        relationLayout.addWidget(self.relEntity2Lbl, 1, 0)
        relationLayout.addWidget(self.relEntity1Cbo, 0, 1)
        relationLayout.addWidget(self.relEntity2Cbo, 1, 1)
        relationLayout.addWidget(self.infoLabel, 2, 0, 1, 2)
        
        # Signals
        self.relationshipCbo.currentIndexChanged.connect(self.relationSelected)

        # Layout
        grid     = QtGui.QGridLayout(self)

        grid.addWidget(QtGui.QLabel("Relationship"),  0, 0)
        grid.addWidget(self.relationshipCbo,  0, 1)
        grid.addWidget(self.relationWgt,  1, 0, 1, 2)

        # Initial behavior
        self.refreshEntityCbo()
        self.relationSelected(0)


    def clear(self):
        self.refreshEntityCbo()
        self.relationSelected(0)



    @property
    def selectedTags(self):
        return self.parent.getSelectedTags()


    def refreshEntityCbo(self):
        selectedTagNames  = [tag.name for tag in self.selectedTags]
        self.relEntity1Cbo.clear()
        self.relEntity2Cbo.clear()
        self.relEntity1Cbo.addItems(selectedTagNames)
        self.relEntity2Cbo.addItems(selectedTagNames)


    def relationSelected(self, index):
        
        if self.relationshipCbo.currentText() == "unspecified":
            self.relEntity2Cbo.setVisible(False)
            self.relEntity1Cbo.setVisible(False)
            self.relEntity1Lbl.setVisible(False)
            self.relEntity2Lbl.setVisible(False)
            self.infoLabel.setVisible(False)
        elif self.relationshipCbo.currentText() == "point":
            self.relEntity2Cbo.setVisible(False)
            self.relEntity1Cbo.setVisible(True)
            self.relEntity1Lbl.setVisible(True)
            self.relEntity2Lbl.setVisible(False)
            self.infoLabel.setVisible(True)                        
            self.relEntity1Lbl.setText("Entity")
        elif self.relationshipCbo.currentText() == "directed":
            self.relEntity2Cbo.setVisible(True)
            self.relEntity1Cbo.setVisible(True)
            self.relEntity1Lbl.setVisible(True)
            self.relEntity2Lbl.setVisible(True)
            self.infoLabel.setVisible(True)  
            self.relEntity1Lbl.setText("Entity from")
            self.relEntity2Lbl.setText("Entity to")
        elif self.relationshipCbo.currentText() == "undirected":
            self.relEntity2Cbo.setVisible(True)
            self.relEntity1Cbo.setVisible(True)
            self.relEntity1Lbl.setVisible(True)
            self.relEntity2Lbl.setVisible(True)
            self.infoLabel.setVisible(True)  
            self.relEntity1Lbl.setText("Entity 1")
            self.relEntity2Lbl.setText("Entity 2")
        else:
            raise ValueError


    def getRelationship(self):

        if self.relationshipCbo.currentText() == "unspecified":
            return None

        for tag in self.selectedTags:
            if tag.name == self.relEntity1Cbo.currentText():
                tag1 = Tag(tag.id, tag.name)
                break

        if self.relationshipCbo.currentText() == "point":
            tag2 = None
        else:
            for tag in self.selectedTags:
                if tag.name == self.relEntity2Cbo.currentText():
                    tag2 = Tag(tag.id, tag.name)
                    break

        return Relationship(self.relationshipCbo.currentText(), tag1, tag2)


    def setRelationship(self, relationship):

        if relationship is None:
            self.relationshipCbo.setCurrentIndex(0)
        else:    
            for noRel, relationType in enumerate(["point", "directed", "undirected"]):
                if relationType == relationship.type:
                    self.relationshipCbo.setCurrentIndex(noRel+1)
                    break

        if self.relationshipCbo.currentText() != "unspecified":
            for i in range(self.relEntity1Cbo.count()):
                if self.relEntity1Cbo.itemText(i) == relationship.entity1.name:
                    self.relEntity1Cbo.setCurrentIndex(i)
                    break

        if not self.relationshipCbo.currentText() in ["unspecified", "point"]:
            for i in range(self.relEntity2Cbo.count()):
                if self.relEntity2Cbo.itemText(i) == relationship.entity2.name:
                    self.relEntity2Cbo.setCurrentIndex(i)
                    break
        


    def loadRow(self, currentParameter):
        """
         Called when a row has been selected in the table listing all the modeling parameters.
         It update the interface with the values associated with this specific parameter.
        """
        self.setRelationship(currentParameter.relationship)


    def loadModelingParameter(self, row = None):
        """
         Call when a new annotation has been selected so that all the modeling parameters
         associated with this annotation are loaded in the parameter list. 
        """
        self.refreshEntityCbo()




