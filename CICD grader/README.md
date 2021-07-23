Grader
=======

- Use Python Version 3 
- virtualenv venv
- source venv/bin/activate
- pip3 install -r requirements.txt

Run grade.py as follows:

```
python3 grade.py <student name> <student bitbucket> <assignment name> <assignment topic> <early deadline> <final deadline>
  <assignment name>: assignment1, assignment2, assignment3, etc.
  <assignment topic>: valid values are 'helm', 'cicd', 's3', 'dynamodb'
  <early deadline> and <final deadline>: format 'YYYY-MM-DD'
```

Example:
```
python3 grade.py xuan https://devdattakulkarni@bitbucket.org/xuanwang5969/assignment3.git assignment3 helm 2021-04-12 2021-04-15  
```


Cloud Computing - Kubernetes/Helm
----------------------------------
- Install Helm v3
- Install KubePlus kubectl connections plugin (export KUBEPLUS_HOME=<path-to-dir in which you have downloaded and untar/unzipped KubePlus plugins)
- Install kubectl
- Make sure that all the above components are accessible on your PATH.
  - Set PATH as follows
    - export PATH=<path-to-Helm-v3-directory>:$KUBEPLUS_HOME/plugins:$PATH

```
python3 grade.py xuan https://devdattakulkarni@bitbucket.org/xuanwang5969/assignment2.git assignment2 helm 2021-03-12 2021-03-10
Cloning repo...

Checking first commit date...
  Sat Mar 13 03:40:58 2021 +0000

Early Deadline Satisied:False
Checking last commit date...
  Fri Mar 19 06:35:27 2021 +0000

Number of late days:9

```

----

Cloud Computing - CICD
-----------------------

Run majority of the tests:
```
python3 grade.py devdatta git@bitbucket.org:devdattakulkarni/assignment42021.git Assignment42021 cicd 2021-04-30 2021-05-03
```

Run application connectivity test:
```
python3 grade.py devdatta git@bitbucket.org:devdattakulkarni/assignment42021.git Assignment42021 connectivity 2021-04-30 2021-05-03
```

Restore the repo to original state:
```
./tools/restore-student-repo-cicd.sh devdatta assignment42021
```
