__author__ = "Christian O'Reilly"


from git import Repo, exc
import os

from PySide import QtGui, QtCore


class GitManager:

	def __init__(self, settings):

		self.localRepoDir = settings.config["GIT"]["local"]
		self.offline = False		

		try:
			self.repo = Repo(self.localRepoDir)
			assert not self.repo.bare

		except (exc.InvalidGitRepositoryError,exc.NoSuchPathError):
			self.repo = Repo.clone_from("ssh://" + settings.config["GIT"]["user"] + "@" + settings.config["GIT"]["remote"], self.localRepoDir)


		self.tryToFetch()

		try:
			# Setup a local tracking branch of a remote branch
			self.repo.create_head('master', self.origin.refs.master).set_tracking_branch(self.origin.refs.master)
		except:
			pass

		self.pull()




	def tryToFetch(self):

		try:
			self.repo.remotes.origin.fetch()
		except:
			if not self.offline:
				msgBox = QtGui.QMessageBox()
				msgBox.setWindowTitle("Error pulling from GIT")
				msgBox.setText("An error occured while trying to access the GIT server. Going in offline mode.")
				msgBox.setStandardButtons(QtGui.QMessageBox.Ok)
				msgBox.exec_()			
				self.offline = True
				return

		if self.offline:
			self.offline = False





	def canRunRemoteCmd(self):		

		if self.repo.is_dirty():
			#modifiedFiles = [os.path.join(self.repo.working_tree_dir, diff.a_path) for diff in self.repo.index.diff(None)]
			modifiedFiles = [diff.a_path for diff in self.repo.index.diff(None)]
			msgBox = QtGui.QMessageBox()
			msgBox.setStandardButtons(QtGui.QMessageBox.Cancel)
			msgBox.setWindowTitle("GIT repository is dirty")
			msgBox.setText("GIT database of annotations is dirty. Do you want to commit uncommited changes" + 
						   " or to cancel the operation? Here is a list of modified files: \n\n" + "\n".join(modifiedFiles))
			button = msgBox.addButton("commit", QtGui.QMessageBox.YesRole)
			msgBox.setDefaultButton(button)
			msgBox.exec_()
			if msgBox.clickedButton() == button:
				self.addFiles(modifiedFiles)			
			else:
				return False


		if self.offline:
			self.tryToFetch()
			if self.offline:
				return False

		return True




	def pull(self):

		if not self.canRunRemoteCmd(): 
			return None

		try:
			fetchInfo = self.repo.remotes.origin.pull()[0]
		except exc.GitCommandError as e:
			print(dir(e), e.command, e.status, e.stderr, e.stdout, e.__cause__)
			raise


		if fetchInfo.flags & fetchInfo.ERROR:
			raise IOError("An error occured while trying to pull the GIT repository from the server. Error flag: '" + 
						  str(fetchInfo.flags) + "', message: '" + str(fetchInfo.note) + "'.")

		return fetchInfo





	def push(self):
		"""
		 Adding the no_thin argument to the GIT push because we had some issues pushing previously.
		 According to http://stackoverflow.com/questions/16586642/git-unpack-error-on-push-to-gerrit#comment42953435_23610917,
		 "a new optimization which causes git to send as little data as possible over the network caused this bug to manifest, 
		  so my guess is --no-thin just turns these optimizations off. From git push --help: "A thin transfer significantly 
          reduces the amount of sent data when the sender and receiver share many of the same objects in common." (--thin is the default)."
		"""

		if not self.canRunRemoteCmd(): 
			return None

		try:
			fetchInfo = self.repo.remotes.origin.push(no_thin=True)[0]
		except exc.GitCommandError as e:
			print(e)
			raise


		if fetchInfo.flags & fetchInfo.ERROR:
			raise IOError("An error occured while trying to push the GIT repository from the server. Error flag: '" + 
						  str(fetchInfo.flags) + "', message: '" + str(fetchInfo.note) + "'.")

		return fetchInfo








	def addFiles(self, files):
		self.repo.index.add(files)
		self.commit()



	def commit(self, msg = "..."): 
		# We don't really need a msg value for this application. Yet, leaving
		# empty commit messages sometimes create problems in GIT. This is why
		# we use this "..." default message.

		try:
			commitObj = self.repo.index.commit(msg)
			#print(commitObj)
		except exc.UnmergedEntriesError as e:
			print(e)
			raise

