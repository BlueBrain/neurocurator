__author__ = "Christian O'Reilly"


from git import Repo, exc
import os

from PySide import QtGui, QtCore

"""
class PasswordDlg(QtGui.QDialog):
	def __init__(self):
		QtGui.QDialog.__init__(self)
		self.textPass = QtGui.QLineEdit(self)

		self.textPass.setEchoMode(QtGui.QLineEdit.Password);
		self.textPass.setInputMethodHints(QtCore.Qt.ImhHiddenText | QtCore.Qt.ImhNoPredictiveText | QtCore.Qt.ImhNoAutoUppercase)


		self.buttonLogin = QtGui.QPushButton('OK', self)
		self.buttonLogin.clicked.connect(self.accept)
		layout = QtGui.QVBoxLayout(self)
		layout.addWidget(self.textPass)
		layout.addWidget(self.buttonLogin)
"""


class GitManager:

	def __init__(self, settings):

		self.localRepoDir = settings.config["GIT"]["local"]
		
		try:
			self.repo = Repo(self.localRepoDir)
			#except exc.NoSuchPathError:
			#	os.makedirs(self.localRepoDir)
			#	self.repo = Repo(self.localRepoDir)
			#
			assert not self.repo.bare

		except (exc.InvalidGitRepositoryError,exc.NoSuchPathError):
			#self.repo = Repo.init(self.localRepoDir, bare=True)
			#assert self.repo.bare
			self.repo = Repo.clone_from("ssh://" + settings.config["GIT"]["user"] + "@" + settings.config["GIT"]["remote"], self.localRepoDir)

		#passwordDlg = PasswordDlg()
		#self.ssh_executable = None
		#if passwordDlg.exec_() == QtGui.QDialog.Accepted:
		#	self.ssh_executable = "sshpass -p '" + passwordDlg.textPass.text() + "' ssh"

		
		self.repo.remotes.origin.fetch()
		#with self.repo.git.custom_environment(GIT_SSH=self.ssh_executable): 
		#	print("fetch")
		#	self.repo.remotes.origin.fetch()
		#	print("after fetch")


		try:
			# Setup a local tracking branch of a remote branch
			self.repo.create_head('master', self.origin.refs.master).set_tracking_branch(self.origin.refs.master)
		except:
			pass

		self.pull()


	def pull(self):
		#with self.repo.git.custom_environment(GIT_SSH_COMMAND=self.ssh_executable): 
		self.repo.remotes.origin.pull()

	def push(self):
		#with self.repo.git.custom_environment(GIT_SSH_COMMAND=self.ssh_executable): 
		self.repo.remotes.origin.push()

	def addFiles(self, files):
		self.repo.index.add(files)
		self.commit()

	def commit(self, msg = ""):
		self.repo.index.commit(msg) 


