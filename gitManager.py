__author__ = "Christian O'Reilly"


from git import Repo, exc
import os

from PySide import QtGui, QtCore


class GitManager:

	def __init__(self, settings):

		self.localRepoDir = settings.config["GIT"]["local"]
		
		try:
			self.repo = Repo(self.localRepoDir)
			assert not self.repo.bare

		except (exc.InvalidGitRepositoryError,exc.NoSuchPathError):
			self.repo = Repo.clone_from("ssh://" + settings.config["GIT"]["user"] + "@" + settings.config["GIT"]["remote"], self.localRepoDir)


		try:
			self.repo.remotes.origin.fetch()

			# Setup a local tracking branch of a remote branch
			self.repo.create_head('master', self.origin.refs.master).set_tracking_branch(self.origin.refs.master)
		except:
			pass

	
		fetchInfo = self.pull()
		if fetchInfo.flags & fetchInfo.ERROR:
			raise IOError("An error occured while trying to pull the GIT repository from the server. Error flag: '" + 
						  str(fetchInfo.flags) + "', message: '" + str(fetchInfo.note) + "'.")



	def pull(self):
		return self.repo.remotes.origin.pull()[0]

	def push(self):
		"""
		 Adding the no_thin argument to the GIT push because we had some issues pushing previously.
		 According to http://stackoverflow.com/questions/16586642/git-unpack-error-on-push-to-gerrit#comment42953435_23610917,
		 "a new optimization which causes git to send as little data as possible over the network caused this bug to manifest, 
		  so my guess is --no-thin just turns these optimizations off. From git push --help: "A thin transfer significantly 
          reduces the amount of sent data when the sender and receiver share many of the same objects in common." (--thin is the default)."
		"""
		return self.repo.remotes.origin.push(no_thin=True)[0]

	def addFiles(self, files):
		self.repo.index.add(files)
		self.commit()

	def commit(self, msg = "..."): 
		# We don't really need a msg value for this application. Yet, leaving
		# empty commit messages sometimes create problems in GIT. This is why
		# we use this "..." default message.
		self.repo.index.commit(msg)


