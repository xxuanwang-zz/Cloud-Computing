import subprocess
import sys
import json
import re
import os
import time
import requests
import datetime
import pytz
import random


utc=pytz.UTC

def _execute_cmd(cmd):
	print(cmd)
	try:
		out = subprocess.Popen(cmd, stdout=subprocess.PIPE,
								stderr=subprocess.PIPE, shell=True).communicate()[0]
		out = out.decode('utf-8')
		out.strip()
		print(out)
		#print(err)
	except Exception as e:
		print(e)
	return out


class AssignmentGrader(object):

	def __init__(self,assignmentName,studentName,studentBitbucket,earlyDeadline,finalDeadline,createOutputFile=True):
		self.finalScore = 0
		self.earlyDeadlineSatisfied = False
		self.numOfLateDays = 0
		self.assignmentName = assignmentName
		self.studentName = studentName
		self.studentBitbucket = studentBitbucket
		self.earlyDeadline = earlyDeadline
		self.finalDeadline = finalDeadline
		self.cwd = os.getcwd()
		self.studentTestdir = self.cwd + "/" + self.studentName
		if not os.path.exists(self.studentTestdir):
			os.mkdir(self.studentTestdir)
		if createOutputFile:
			self.outputfile = self.studentName + ".out"
			self.fp = open(self.studentTestdir + "/" + self.outputfile, 'w')

	def start_grading(self, final_commit_cmd=''):
		self._clone_repo()
		self._check_first_commit()
		self._check_final_commit(final_commit_cmd=final_commit_cmd)

	def _clone_repo(self):
		print("Cloning repo...")
		os.chdir(self.studentTestdir)
		gitCloneCmd = 'git clone ' + self.studentBitbucket
		_execute_cmd(gitCloneCmd)
		os.chdir(self.cwd)

	def _check_first_commit(self):
		print("Checking first commit date...")
		cwd = os.getcwd()
		os.chdir(self.studentTestdir + "/" + self.assignmentName)
		cmd = "git log --pretty=oneline | awk '{print $1}' | tail -1 | xargs git show | head -3 | grep Date | cut -d' ' -f2-"
		commitDate = _execute_cmd(cmd)
		commitDate = commitDate.strip()
		# commitDate: Sat Mar 13 03:40:58 2021 +0000
		date_time_obj = datetime.datetime.strptime(commitDate, '%a %b %d %H:%M:%S %Y %z').replace(tzinfo=utc)
		#print(date_time_obj)
		early_deadline_obj = datetime.datetime.strptime(self.earlyDeadline, '%Y-%m-%d').replace(tzinfo=utc)
		#print(early_deadline_obj)
		delta = date_time_obj - early_deadline_obj
		num_of_days = delta.days
		#print("Early Deadline Satisied:" + str(self.earlyDeadlineSatisfied))
		if num_of_days <= 0:
			self.earlyDeadlineSatisfied = True
		print("Early Deadline Satisied:" + str(self.earlyDeadlineSatisfied))
		os.chdir(cwd)

	def _check_final_commit(self, final_commit_cmd=''):
		print("Checking last commit date...")
		cwd = os.getcwd()
		os.chdir(self.studentTestdir + "/" + self.assignmentName)
		cmd = final_commit_cmd
		if cmd == '':
			cmd = "git log --pretty=oneline | awk '{print $1}' | head -1 | xargs git show | head -3 | grep Date | cut -d' ' -f2-"
		commitDate = _execute_cmd(cmd)
		commitDate = commitDate.strip()
		date_time_obj = datetime.datetime.strptime(commitDate, '%a %b %d %H:%M:%S %Y %z').replace(tzinfo=utc)
		#print(date_time_obj)
		final_submission_date_obj = datetime.datetime.strptime(self.finalDeadline, '%Y-%m-%d').replace(tzinfo=utc)
		#print(final_submission_date_obj)
		delta = date_time_obj - final_submission_date_obj
		self.numOfLateDays = delta.days
		if self.numOfLateDays < 0:
			self.numOfLateDays = 0
		print("Number of late days:" + str(self.numOfLateDays))
		os.chdir(cwd)

	def conclude_grading(self):
		if not self.earlyDeadlineSatisfied:
			self.finalScore = self.finalScore - 3

		if self.numOfLateDays > 0:
			count = 0
			while count < self.numOfLateDays:
				self.finalScore = self.finalScore - 5
				count = count + 1

		self.fp.write("-------------------------------\n")
		self.fp.write("Number of late days:" + str(self.numOfLateDays) + "\n")
		self.fp.write("Early deadline satisfied:" + str(self.earlyDeadlineSatisfied) + "\n")		
		self.fp.write("Final score:" + str(self.finalScore) + "\n")
		self.fp.write("-------------------------------\n")
		self.fp.close()

class CICDGrader(AssignmentGrader):

	def __init__(self, assignmentName,studentName,studentBitbucket,earlyDeadline,finalDeadline,createOutputFile=True):
		super(CICDGrader,self).__init__(assignmentName,studentName,studentBitbucket,earlyDeadline,finalDeadline,createOutputFile=createOutputFile)
		self.testingDir = self.studentTestdir + "/" + self.assignmentName
		self.jenkinsAssignmentName = self.assignmentName.capitalize()

	def _get_jenkins_details(self):
		jenkinsVM = ''
		jenkinsUser = ''
		cwd = os.getcwd()
		os.chdir(self.studentTestdir + "/" + self.assignmentName)
		fp = open("README.txt", "r")
		lines = fp.readlines()
		for line in lines:
			if 'JenkinsIP' in line:
				line = line.replace("http://","")
				parts = line.split(":")
				jenkinsVM = parts[1].strip()
				jenkinsVM = jenkinsVM.replace("http://", "")
				parts1 = jenkinsVM.split(":")
				if len(parts1) > 0:
					jenkinsVM = parts1[0]
			if 'JenkinsUser' in line:
				parts = line.split(":")
				jenkinsUser = parts[1].strip()
		os.chdir(cwd)
		jenkinsVM = jenkinsVM.strip()
		jenkinsUser = jenkinsUser.strip()
		jenkinsUser = "ubuntu"
		print("JenkinsIP -> " + jenkinsVM)
		print("JenkinsUser -> " + jenkinsUser)
		return jenkinsVM, jenkinsUser

	def _get_application_url(self):
		cwd = os.getcwd()
		os.chdir(self.studentTestdir + "/" + self.assignmentName)
		fp = open("README.txt", "r")
		applicationURL = ""
		lines = fp.readlines()
		for line in lines:
			if 'Application' in line:
				parts = line.split("http://")
				print(parts)
				if len(parts) > 1:
					applicationURL = parts[1].strip()
				else:
					parts1 = line.split(":")
					applicationURL = parts1[1].strip()
				break
		os.chdir(cwd)
		print("Application URL:" + applicationURL)
		return applicationURL

	def _get_jenkins_next_build_number(self, jenkinsVM, jenkinsUser):
		jenkinsFolderName = self._get_jenkins_folder_name(jenkinsVM, jenkinsUser)
		scpPrefix = self._get_scp_prefix(jenkinsVM, jenkinsUser)
		remoteFile = "\"~/.jenkins/jobs/" + jenkinsFolderName + "/nextBuildNumber\" "
		#cmd = scpPrefix+ ":~/.jenkins/jobs/" + jenkinsFolderName + "/nextBuildNumber " + self.studentTestdir + "/."
		cmd = scpPrefix + ":" + remoteFile + self.studentTestdir + "/."
		#print(cmd)
		_execute_cmd(cmd)
		fp = open(self.studentTestdir + "/nextBuildNumber", "r")
		lines = fp.readlines()
		nextBuildNumber = "-1"
		if len(lines) > 0:
			nextBuildNumber = lines[0]
			nextBuildNumber = nextBuildNumber.strip()
		return nextBuildNumber

	def _replace_and_commit(self, fileName):
		catCmd = 'cat testdata/' + fileName
		_execute_cmd(catCmd)

		cpCmd = 'cp -f testdata/' + fileName + ' ' + self.testingDir + "/application.py"
		#print(cpCmd)
		_execute_cmd(cpCmd)
		cwd = os.getcwd()
		os.chdir(self.testingDir)

		randNumber = random.randrange(100, 1000, 3)
		randString = "test-" + str(randNumber)
		sedCmd = "sed -i .bak 's/test/" + randString + "/g' application.py"
		_execute_cmd(sedCmd)
		
		gitAdd = 'git add application.py'
		_execute_cmd(gitAdd)

		gitCommit = 'git commit -m "Adding ' + fileName + "\""
		_execute_cmd(gitCommit)

		gitPush = 'git push origin master'
		_execute_cmd(gitPush)

		os.chdir(cwd)

	def _get_ssh_prefix(self, jenkinsVM, jenkinsUser):
		sshPrefix = "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null " + jenkinsUser + "@" + jenkinsVM 
		return sshPrefix

	def _get_scp_prefix(self, jenkinsVM, jenkinsUser):
		scpPrefix = "scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null " + jenkinsUser + "@" + jenkinsVM
		return scpPrefix

	def _get_jenkins_folder_name(self, jenkinsVM, jenkinsUser):
		jenkinsFolderName = ''
		sshPrefix = self._get_ssh_prefix(jenkinsVM, jenkinsUser)
		cmd = sshPrefix + " \"ls ~/.jenkins/workspace/ \""
		jenkinsFolderName = _execute_cmd(cmd)
		jenkinsFolderName = jenkinsFolderName.strip()
		print("Jenkins Folder Name:" + jenkinsFolderName)
		jenkinsFolderNameEscaped = re.escape(jenkinsFolderName)
		print("Jenkins Folder Name escaped:" + jenkinsFolderNameEscaped)
		return jenkinsFolderNameEscaped

	def _check_webhook_trigger_received(self, jenkinsVM, jenkinsUser, fileName):
		print("1. Test case - Webhook received - 10 points")
		points = 10
		# localfile = read the local file
		# remotefile = read the remote file
		# diff localfile remotefile --> there should not be any difference
		print("Waiting 40 seconds..")
		time.sleep(40) # wait 10 seconds to allow the webhook to be received
		jenkinsFolderName = self._get_jenkins_folder_name(jenkinsVM, jenkinsUser)
		scpPrefix = self._get_scp_prefix(jenkinsVM, jenkinsUser)
		remoteFile = "\"~/.jenkins/workspace/" + jenkinsFolderName + "/application.py\" "
		print("Remote File:" + remoteFile)
		scpCmd = scpPrefix + ":" + remoteFile + self.studentTestdir + "/."
		_execute_cmd(scpCmd)

		diffCmd = "diff " + self.studentTestdir + "/" + self.assignmentName + "/application.py " + " " + self.studentTestdir + "/application.py"
		diffValue = _execute_cmd(diffCmd)
		#print("File Diff Value:" + str(diffValue))
		diffValue = diffValue.strip()
		if diffValue == '':
			self.finalScore = self.finalScore + points
			webhook_trigger = 'passed'
			self.fp.write('------------- Test case: Webhook Triggered? ---------------- ' + webhook_trigger + '\n')
			self.fp.write('Running score:' + str(self.finalScore) + "\n")
		else:
			webhook_trigger = 'failed'
			self.fp.write('------------- Test case: Webhook Triggered? ---------------- ' + webhook_trigger + '\n')
			self.fp.write('Running score:' + str(self.finalScore) + "\n")

	def _check_build_triggered(self, jenkinsVM, jenkinsUser, nextBuildNumber):
		print("2. Test case - Build triggered - 10 points")
		points = 10
		# Check that nextBuildNumber directory is created
		jenkinsFolderName = self._get_jenkins_folder_name(jenkinsVM, jenkinsUser)
		cmd = " \"ls -ltr ~/.jenkins/jobs/" + jenkinsFolderName + "/builds\""
		#print(cmd)
		sshCmd = "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null " + jenkinsUser + "@" + jenkinsVM + cmd
		#print(sshCmd)
		lines = _execute_cmd(sshCmd)
		foundBuild = False
		for line in lines.split("\n"):
			line = " ".join(line.split())
			#print("$$$ " + line)
			parts = line.split(" ")
			if len(parts) == 9:
				dirName = parts[8].strip()
				#print("Dirname:" + dirName)
				if dirName == nextBuildNumber:
					foundBuild = True
					self.finalScore = self.finalScore + points
					build_started = 'passed'
					self.fp.write('------------- Test case: Build Started? ---------------- ' + build_started + '\n')
					self.fp.write('Running score:' + str(self.finalScore) + "\n")
		if not foundBuild:
			build_started = 'failed'
			self.fp.write('------------- Test case: Build Started? ---------------- ' + build_started + '\n')
			self.fp.write('Running score:' + str(self.finalScore) + "\n")

	def _get_image_name(self):
		imageName = ''
		cwd = os.getcwd()
		os.chdir(self.testingDir)

		cmd = "grep image: *"
		output = _execute_cmd(cmd)
		for line in output.split("\n"):
			if "image:" in line:
				parts = line.split(":")
				imageName = parts[2].strip()
				imageName = imageName.replace("\"","")
				break
		os.chdir(cwd)
		return imageName

	def _get_container_count(self, imageName, jenkinsVM, jenkinsUser):
		sshPrefix = self._get_ssh_prefix(jenkinsVM, jenkinsUser)
		dockerImages = sshPrefix + " \"docker images | grep " + imageName + " | wc -l \""
		imageCount = _execute_cmd(dockerImages)
		imageCount = imageCount.strip()
		return imageCount

	def _check_container_built(self, jenkinsVM, jenkinsUser, currentContainerCount):
		print("3. Test case - Container built - 15 points")
		points = 15
		imageName = self._get_image_name()
		print("Image to search:" + imageName)
		newContainerCount = self._get_container_count(imageName, jenkinsVM, jenkinsUser)
		print("New container count:" + str(newContainerCount))
		if int(newContainerCount) - int(currentContainerCount) == 1:
			container_built = 'passed'
			self.finalScore = self.finalScore + points
			self.fp.write('------------- Test case: Container built? ---------------- ' + container_built + '\n')
			self.fp.write('Running score:' + str(self.finalScore) + "\n")
		else:
			container_built = 'failed'
			self.fp.write('------------- Test case: Container built? ---------------- ' + container_built + '\n')
			self.fp.write('Running score:' + str(self.finalScore) + "\n")

	def _check_service_yaml_defined(self):
		points = 10
		print("Test case - Service yaml defined? - 10 points")
		cwd = os.getcwd()
		os.chdir(self.testingDir)

		serviceDefined = False
		cmd = "grep Service *.yaml"
		output = _execute_cmd(cmd)
		for line in output.split("\n"):
			if "kind: Service" in line:
				service_defined = 'passed'
				serviceDefined = True
				self.finalScore = self.finalScore + points
				self.fp.write('------------- Test case: Service YAML defined? ---------------- ' + service_defined + '\n')
				self.fp.write('Running score:' + str(self.finalScore) + "\n")
				break
		if not serviceDefined:
			service_defined = 'failed'
			self.fp.write('------------- Test case: Service YAML defined? ---------------- ' + service_defined + '\n')
			self.fp.write('Running score:' + str(self.finalScore) + "\n")
		os.chdir(cwd)

	def _check_deployment_triggered(self, jenkinsVM, jenkinsUser, buildNumber, deploymentTriggered):
		print(" 4. Test case - Deployment triggered? - 20 points")
		deploymentYesPoints = 10
		deploymentNoPoints = 10

		jenkinsFolderName = self._get_jenkins_folder_name(jenkinsVM, jenkinsUser)
		scpPrefix = self._get_scp_prefix(jenkinsVM, jenkinsUser)
		remoteFile = "\"~/.jenkins/jobs/" + jenkinsFolderName + "/builds/" + buildNumber + "/log" + "\" "

		if deploymentTriggered:
			#remoteFile = "\"~/.jenkins/jobs/" + jenkinsFolderName + "/builds/" + buildNumber + "/log" + "\" "
			#scpCmd = scpPrefix + ":~/.jenkins/jobs/" + jenkinsFolderName + "/builds/" + buildNumber + "/log " + self.studentTestdir + "/good-application-log"
			scpCmd = scpPrefix + ":" + remoteFile + self.studentTestdir + "/good-application-log"
			_execute_cmd(scpCmd)
			passed = False
			try:
				logfile = open(self.studentTestdir + "/good-application-log", "r")
				lines = logfile.readlines()

				for line in lines:
					if 'Done deploying' in line:
						passed = True
						break
			except Exception as e:
				print(e)
			if passed:
				self.finalScore = self.finalScore + deploymentYesPoints
				deploymentTriggered = 'passed'
				self.fp.write('------------- Test case: Deployment Trigger required? ---------------- ' + deploymentTriggered + '\n')
				self.fp.write('Running score:' + str(self.finalScore) + "\n")
			else:
				deploymentTriggered = 'failed'
				self.fp.write('------------- Test case: Deployment Trigger required? ---------------- ' + deploymentTriggered + '\n')
				self.fp.write('Running score:' + str(self.finalScore) + "\n")
		else:
			#scpCmd = scpPrefix + ":~/.jenkins/jobs/" + jenkinsFolderName + "/builds/" + buildNumber + "/log " + self.studentTestdir + "/bad-application-log"
			scpCmd = scpPrefix + ":" + remoteFile + self.studentTestdir + "/bad-application-log"
			_execute_cmd(scpCmd)

			failed = False
			try:	
				logfile = open(self.studentTestdir + "/bad-application-log", "r")
				lines = logfile.readlines()
				for line in lines:
					if 'Logical operation result is TRUE' in line:
						failed = True
						break
			except Exception as e:
				print(e)
			if failed:
				deploymentTriggered = 'failed'
				self.fp.write('------------- Test case: Deployment Trigger not required? ---------------- ' + deploymentTriggered + '\n')
				self.fp.write('Running score:' + str(self.finalScore) + "\n")
			else:
				self.finalScore = self.finalScore + deploymentNoPoints
				deploymentTriggered = 'passed'
				self.fp.write('------------- Test case: Deployment Trigger not required? ---------------- ' + deploymentTriggered + '\n')
				self.fp.write('Running score:' + str(self.finalScore) + "\n")

	def _check_application_deployed(self):
		print(" 5. Test case - Application updated? - 15 points")
		points = 15
		applicationURL = self._get_application_url()
		if applicationURL == '':
			self.fp.write('------------- Test case: Application connectivity ---------------- \n')
			self.fp.write('Application URL: Not provided\n' + applicationURL)
			self.fp.write('Running score:' + str(self.finalScore) + "\n")
			return

		# Read current final score
		outputFile = self.studentName + ".out"
		print("O/P file:" + outputFile)
		print("CWD:" + os.getcwd())
		fp = open(self.studentTestdir + "/" + outputFile, "r")
		lines = fp.readlines()
		currentFinalScore = 0
		print(lines)
		for line in lines:
			#print("$$$ line:" + line)
			if 'Final score' in line:
				parts = line.split(":")
				finalScore = parts[1].strip()
				currentFinalScore = int(finalScore)
				break
		print("Current final score:" + str(currentFinalScore))
		fp.close()

		applicationURL = "http://" + applicationURL
		print("Application URL:" + applicationURL)
		r = requests.get(applicationURL)
		status_code = r.status_code
		print("Status code:" + str(status_code))
		if status_code == 200:
			responseBody = r.text
			print("Response body:" + responseBody)
			passingTest = False
			if "Passing test" in responseBody:
				fp = open(self.studentTestdir + "/" + outputFile, "a+") # open in append mode
				currentFinalScore = currentFinalScore + points
				connectivity = 'passed'
				fp.write('------------- Test case: Check stack connectivity ---------------- ' + connectivity + '\n')
				fp.write('Updated Final score:' + str(currentFinalScore) + "\n")
				fp.close()
			if "Failing test" in responseBody:
				fp = open(self.studentTestdir + "/" + outputFile, "a+") # open in append mode
				connectivity = 'failed'
				fp.write('------------- Test case: Check stack connectivity ---------------- ' + connectivity + '\n')
				fp.write('Updated Final score:' + str(currentFinalScore) + "\n")
				fp.close()

	def _run_test(self, jenkinsVM, jenkinsUser, fileName):
		self.fp.write("-- Checking " + fileName + " --\n")
		self._replace_and_commit(fileName)
		nextBuildNumber = self._get_jenkins_next_build_number(jenkinsVM, jenkinsUser)
		print("Next Build Number:" + nextBuildNumber)
		imageName = self._get_image_name()
		print("Image name:" + imageName)
		currentContainerCount = self._get_container_count(imageName, jenkinsVM, jenkinsUser)
		print("Current container count:" + str(currentContainerCount))
		self._check_webhook_trigger_received(jenkinsVM, jenkinsUser, fileName) # 10 points
		self._check_build_triggered(jenkinsVM, jenkinsUser, nextBuildNumber) # 10 points
		if fileName == 'good-application.py':
			self._check_container_built(jenkinsVM, jenkinsUser, currentContainerCount) # 10 points
			self._check_deployment_triggered(jenkinsVM, jenkinsUser, nextBuildNumber, True) # 8 points
		if fileName == 'bad-application.py':
			self._check_deployment_triggered(jenkinsVM, jenkinsUser, nextBuildNumber, False) # 7 points

	def _restore_original_files(self):
		print("Restoring original file...")

		# Restore original
		cpCmd = 'cp -f ' + self.studentTestdir + '/original-application.py ' + self.testingDir + "/application.py" 
		_execute_cmd(cpCmd)

		cwd = os.getcwd()
		os.chdir(self.testingDir)

		gitAdd = 'git add application.py'
		_execute_cmd(gitAdd)

		gitCommit = 'git commit -m "Original application.py ' + "\""
		_execute_cmd(gitCommit)

		gitPush = 'git push origin master'
		_execute_cmd(gitPush)

		os.chdir(cwd)
		print("Done")

	def start_grading(self):
		final_commit_cmd = "git log --pretty=oneline | grep -v good-application | grep -v bad-application| grep -v Original | grep -v Merge | grep -v 'Grading related fix' | awk '{print $1}' | head -1 | xargs git show | head -3 | grep Date | cut -d' ' -f2-"
		AssignmentGrader.start_grading(self, final_commit_cmd=final_commit_cmd)
		jenkinsVM, jenkinsUser = self._get_jenkins_details()

		print("Testing started...")
		print("Test scenario 1: Good application.py")
		# Save original
		cpCmd = 'cp ' + self.testingDir + "/application.py " + self.studentTestdir + "/original-application.py"
		_execute_cmd(cpCmd)

		# Test case 1: Passing test
		self._run_test(jenkinsVM, jenkinsUser, 'good-application.py')
		print("-----------")
		print("Waiting 40 seconds before starting next test...")
		time.sleep(40) # sleep for 20 seconds

		# Test case 2: Failing test
		print("Test scenario 1: Bad application.py")
		self._run_test(jenkinsVM, jenkinsUser, 'bad-application.py')

		self._check_service_yaml_defined()

		AssignmentGrader.conclude_grading(self)

		# Restore original - Not triggering restore as it will change the contents of the application URL
		# self._restore_original_files()

class ConnectivityChecker(CICDGrader):

	def __init__(self, assignmentName,studentName,studentBitbucket,earlyDeadline,finalDeadline):
		super(ConnectivityChecker,self).__init__(assignmentName,studentName,studentBitbucket,earlyDeadline,finalDeadline,createOutputFile=False)

	def check_connectivity(self):
		self._check_application_deployed()

class HelmChartAssignmentGrader(AssignmentGrader):

	def __init__(self, assignmentName,studentName,studentBitbucket,earlyDeadline,finalDeadline):
		super(HelmChartAssignmentGrader,self).__init__(assignmentName,studentName,studentBitbucket,earlyDeadline,finalDeadline)

	def start_grading(self):
		AssignmentGrader.start_grading(self)

		print("Testing started...")
		releaseName1 = 'wp1'
		releaseName2 = 'wp2'
		self._deploy_chart(releaseName=releaseName1)
		self._deploy_chart(releaseName=releaseName2)

		# verify
		print("Waiting for 180 seconds before starting verification...")
		count = 180
		while count > 0:
			print('.', end='',flush=True)
			time.sleep(1)
			count = count - 1

		print("\nStarting verification " + releaseName1)
		self._check_num_of_pods(releaseName=releaseName1)
		self._check_nodeport_service(releaseName=releaseName1)
		self._check_kubectl_connections(releaseNameToCheck=releaseName1,releaseNameToAvoid=releaseName2)
		time.sleep(10)
		self._check_stack_is_accessible(releaseName=releaseName1)
		self._check_mysql_service_is_not_accessible(releaseName=releaseName1)

		print("Starting verification " + releaseName2)
		self._check_num_of_pods(releaseName=releaseName2)
		self._check_nodeport_service(releaseName=releaseName2)
		self._check_kubectl_connections(releaseNameToCheck=releaseName2,releaseNameToAvoid=releaseName1)
		time.sleep(10)
		self._check_stack_is_accessible(releaseName=releaseName2)
		self._check_mysql_service_is_not_accessible(releaseName=releaseName2)

		releases = []
		releases.append(releaseName1)
		releases.append(releaseName2)

		for release in releases:
			cmd = 'helm delete ' + release
			_execute_cmd(cmd)

		AssignmentGrader.conclude_grading(self)

	def _deploy_chart(self,releaseName='wp'):
		print("Deploying chart " + releaseName + " .....")
		chartPath = "./" + self.studentName + "/assignment3/wp-chart"
		password = releaseName + "123"
		cmd = 'helm install ' + releaseName + ' ' + chartPath + ' --set resourceName=' + releaseName + ' --set wpReplicas=2 --set dbPassword=' + password
		_execute_cmd(cmd)

	def _check_num_of_pods(self,releaseName='wp'):
		points = 10
		print("Checking number of Pods for " + releaseName + " ... " + str(points) + ' points')
		cmd = 'kubectl get pods | grep ' + releaseName + ' | wc -l'
		output = _execute_cmd(cmd)
		output = output.strip()
		podCheck = 'failed'
		if output == '3':
			self.finalScore = self.finalScore + points
			podCheck = 'passed'
		self.fp.write('------------- Test case: Num of Pods ' + releaseName + ' ---------------- ' + podCheck + '\n')
		self.fp.write('Running score:' + str(self.finalScore) + "\n")

	def _check_nodeport_service(self,releaseName='wp'):
		points = 10
		print("Checking Wordpress service type for " + releaseName + " ... " + str(points) + ' points')
		cmd = 'kubectl get svc |grep ' + releaseName + ' | grep NodePort | grep -v 3306 | wc -l'
		output = _execute_cmd(cmd)
		output = output.strip()
		serviceCheck = 'failed'
		if output == '1':
			self.finalScore = self.finalScore + points
			serviceCheck = 'passed'
		self.fp.write('------------- Test case: Service Type ' + releaseName + ' ---------------- ' + serviceCheck + '\n')
		self.fp.write('Running score:' + str(self.finalScore) + "\n")

	def _check_kubectl_connections(self,releaseNameToCheck='wp1',releaseNameToAvoid='wp2'):
		points = 10
		print("Checking connections for " + releaseNameToCheck + " ... " + str(points) + ' points')
		connectionsCheck = 'failed'
		svcCmd = 'kubectl get svc | grep ' + releaseNameToCheck
		output = _execute_cmd(svcCmd)
		output = output.strip()
		serviceName = ''
		for line in output.split('\n'):
			if 'NodePort' in line:
				parts = line.split(" ")
				serviceName = parts[0].strip()
				print("Service:" + serviceName)
				break

		cmd = 'kubectl connections Service ' + serviceName + ' default -i ServiceAccount:default,Namespace:default -o flat | grep ' + releaseNameToAvoid + ' | wc -l'
		output = _execute_cmd(cmd)
		output = output.strip()
		if output == '0':
			self.finalScore = self.finalScore + points
			connectionsCheck = 'passed'

		self.fp.write('------------- Test case: Separate stacks ' + releaseNameToCheck + ' ---------------- ' + connectionsCheck + '\n')
		self.fp.write('Running score:' + str(self.finalScore) + "\n")

	def _check_stack_is_accessible(self,releaseName='wp'):
		# Check all the release pods are 'RUNNING' - 5 points
		# Check curl to the WordPress Service returns successful response - 5 points
		# Check
		points = 15
		connectivity = 'failed'
		print("Checking stack connectivity for " + releaseName + " ... " + str(points) + ' points')
		node_cmd = "kubectl describe node | grep -i external | awk '{print $2}'"
		node_ip = _execute_cmd(node_cmd)
		if node_ip == '':
			node_cmd = "kubectl describe node | grep -i internal | awk '{print $2}'"
			node_ip = _execute_cmd(node_cmd)
		node_ip = node_ip.strip()
		print("Node IP:" + node_ip)

		cmd = 'kubectl get svc |grep ' + releaseName + ' | grep NodePort | grep -v 3306'
		output = _execute_cmd(cmd)
		output = output.strip()
		parts = output.split(" ")
		nodePort = ''
		for p in parts:
			if '80' in p:
				parts1 = p.split(":")
				p1 = parts1[1]
				parts2 = p1.split("/")
				p2 = parts2[0]
				nodePort = p2.strip()
				print(nodePort)
				break

		url = 'http://' + node_ip + ":" + nodePort + "/wp-admin/install.php"
		print(url)
		r = requests.get(url)
		status_code = r.status_code
		print("Status code:" + str(status_code))
		if status_code == 200:
			self.finalScore = self.finalScore + points
			connectivity = 'passed'
			self.fp.write('------------- Test case: Check stack connectivity ' + releaseName + ' ---------------- ' + connectivity + '\n')
			self.fp.write('Running score:' + str(self.finalScore) + "\n")

	def _check_mysql_service_is_not_accessible(self, releaseName='wp'):
		points = 5
		print("Checking Mysql service reachability " + releaseName + " ... " + str(points) + ' points')
		mysqlServiceTypeCheck = 'failed'
		cmd = "kubectl get svc | grep " + releaseName + " | grep 3306 | grep ClusterIP | wc -l"
		output = _execute_cmd(cmd)
		output = output.strip()
		if output == '1':
			self.finalScore = self.finalScore + points
			mysqlServiceTypeCheck = 'passed'
			self.fp.write('------------- Test case: Check Mysql Service Type ' + releaseName + ' ---------------- ' + mysqlServiceTypeCheck + '\n')
			self.fp.write('Running score:' + str(self.finalScore) + "\n")

if __name__ == '__main__':
	if len(sys.argv) < 7:
		print("python grade.py <student name> <student bitbucket> <assignment name> <assignment topic> <early deadline> <final deadline>")
		print("  <assignment name>: assignment1, assignment2, assignment3, etc.")
		print("  <assignment topic>: valid values are 'helm', 'cicd', 'connectivity', 's3', 'dynamodb'")
		print("  <early deadline> and <final deadline>: format 'YYYY-MM-DD' ")
		sys.exit(0)
	studentName = sys.argv[1]
	studentBitbucket = sys.argv[2]
	assignmentName = sys.argv[3]
	assignmentTopic = sys.argv[4]
	earlyDeadline = sys.argv[5]
	finalDeadline = sys.argv[6]

	if assignmentTopic == 'helm':
		helmchartGrader = HelmChartAssignmentGrader(assignmentName,studentName,studentBitbucket,earlyDeadline,finalDeadline)
		helmchartGrader.start_grading()
	if assignmentTopic == 'cicd':
		cicdGrader = CICDGrader(assignmentName,studentName,studentBitbucket,earlyDeadline,finalDeadline)
		cicdGrader.start_grading()
	if assignmentTopic == 'connectivity':
		connectivityChecker = ConnectivityChecker(assignmentName,studentName,studentBitbucket,earlyDeadline,finalDeadline)
		connectivityChecker.check_connectivity()
	print("Done")