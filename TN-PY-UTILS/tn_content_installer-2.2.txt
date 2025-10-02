## Script to populate a TN installation from a snapshot.
## Version 2.2

import sys
import json
import os
import requests
import re

## Function:  Read file to json object
## Returns: json object, or text string if it fails
def readJsonOrTextFile(file_path):
    try:
        with open(file_path, "r") as file:
            content = file.read()
    except FileNotFoundError:
        print(f"The file {file_path} does not exist.")
        return None
    except IOError:
        print(f"An error occurred while trying to read the file {file_path}.")
        return None

    try:
        jsonObj = json.loads(content)
    except ValueError as e: # includes simplejson.decoder.JSONDecodeError
        return content
    
    return jsonObj

## BEGIN main program:
print("\n######### Truenumber Content Install v1.4 Started #############\n")
# get api urls from environment or from hardcoded defaults
try:
    tnTriggerBase = os.environ["TN_TRIGGER_API_BASE"]  ## Get Trigger API base url
except KeyError:
    tnTriggerBase = input("Environmnet var TN_TRIGGER_API_BASE undefined, enter url (Enter for default):")
    if tnTriggerBase == "":
        tnTriggerBase = 'http://truenumbers-trigger-api:8082'

try:
    tnArtifactBase = os.environ["TN_ARTIFACT_API_BASE"]  ## Get Trigger API base url
except KeyError:
    tnArtifactBase = input("Environmnet var TN_ARTIFACT_API_BASE undefined, enter url (Enter for default):")
    if tnArtifactBase == "":
         tnArtifactBase = 'http://truenumbers-artifact-api:8081'

try:
    tnRestBase = os.environ["TN_REST_API_BASE"]  ## Get Trigger API base url
except KeyError:
    tnRestBase = input("Environmnet var TN_REST_API_BASE undefined, enter url (Enter for default):")
    if tnRestBase == "":
         tnRestBase = 'http://truenumbers-rest-api:8080'

    
print("Using APIs at " + tnRestBase.split("/")[2] + "\n")

# Get list of numberspaces from subdirectory names:
dList = []
for x in os.walk("."):
    dList.append(x[1])

# All dirs in the root dir of the install are expected to be numberspaces, unless first char is underscore or dot

archiveList = [x for x in dList[0] if  not x.startswith("_") and not x.startswith(".")] ## List if nspace archive dirs

# Get list of nspaces from the API
result = requests.get(tnRestBase + "/v2/numberflow/numberspace")
nsList = result.json()

# Clean of the prepended system stuff leaving the nspace name:
cleanNsList = [x.split("/")[1] for x in nsList["numberspaces"]]

## Process each numberspace archive subdirectory

for nsDirName in archiveList:
    keyPress = input("\nDo you want to load numberspace " + nsDirName + "? (Y/N): ")
    if keyPress.upper() != "Y":
        print(" *** Skipping numberspace ",nsDirName, " ***")
        continue
    
# Ask user about deleting existing numberspace before making a new one

    if nsDirName not in cleanNsList:
        print("Creating numberspace ",nsDirName)
        result = requests.post(tnRestBase + "/v2/numberflow/numberspace", json={"numberspace":nsDirName})
    else:
        keyPress = input("Numberspace " + nsDirName + " exists, delete its content? (Y/N): ")
        if keyPress.upper()[0] == "Y":
            res = requests.get(tnTriggerBase + "/v1/trigger-definitions")
            trigArray = res.json()["triggerDefinitions"]
            for trig in trigArray:
                trigSpace = str(trig["numberspace"])
                if trigSpace.endswith("/" + nsDirName):
                    try:
                        print("deleting trigger ",trig["id"])
                        res = requests.delete(tnTriggerBase + "/v1/trigger-definitions/" + trig["id"]) # remove if its there
                    except:
                        print("couldn't delete trigger ",trig["id"])
            result = requests.delete(tnRestBase + "/v2/numberflow/numberspace", params={"numberspace":nsDirName})
            print(" --> All " + nsDirName + "content deleted")
            result = requests.post(tnRestBase + "/v2/numberflow/numberspace", json={"numberspace":nsDirName})

# Next, upload numberspace dumpfile from subdirectory 

    nspaceFileName = nsDirName + "/TRUENUMBERS.txt"
    print("\nLoading numberspace: " + nsDirName)
    tnPayload = readJsonOrTextFile(nspaceFileName)
    artifactIdSet = []
    if tnPayload != None:
        if type(tnPayload) != dict:  # wrap text payload in JSON
            artifactFindString = tnPayload
            tnPayload = {"trueStatement":tnPayload, "noReturn":True}
        else:
            artifactFindString = json.dumps(tnPayload)
        artifactIdSet = set(re.findall(r'_system:artifact:[a-zA-Z0-9-_:]+', artifactFindString))
        
        res = requests.post(tnRestBase + "/v2/numberflow/numbers", 
                        params={"numberspace":nsDirName}, json = tnPayload)
        
        print("\nPosted to " + nsDirName + ", HTTP return code = ",str(res.status_code))
       
        # Next, load artifacts if any
        artifactDirName = nsDirName + "/files"
        if os.path.exists(artifactDirName):
            print("File-valued TNs in " + nsDirName + " installing file artifacts")
            # Remove that ID before loading
            if len(artifactIdSet) > 0:
                for artifactId in artifactIdSet:
                    fname = artifactDirName + "/" + artifactId.split(":")[-1]
                    fnameParts = fname.split("_")
                    fnameExt = "." + fnameParts.pop()
                    fname = "_".join(fnameParts) + fnameExt
                    res = requests.delete(tnArtifactBase + "/v1/artifact/" + artifactId)
                    res = requests.post(tnArtifactBase + "/v1/artifact/" + artifactId, files={"artifact":open(fname, 'r')})
                    print("\nPosted artifact "+ fname + ", HTTP return code = " + str(res.status_code))
    else:
        print("\nNo TNs or files to load into " + nsDirName)

    # Lastly, upload trigger dumps
    triggerFileName = nsDirName + "/TRIGGERS.txt"
    jsonTrigs = readJsonOrTextFile(nsDirName + "/TRIGGERS.txt") 
    if jsonTrigs != None:
        for trig in jsonTrigs["triggerDefinitions"]:
            theId = trig.pop("id","")
            parm = {"loadHistoricData" : 0}
            res = requests.delete(tnTriggerBase + "/v1/trigger-definitions/" + theId) # remove if its there
            print(" installing trigger " + trig["name"] + " to " + nsDirName)
            res = requests.post(tnTriggerBase + "/v1/trigger-definition", params=parm, json = trig)
            if res.status_code != 200 and res.status_code != 201:
                print("Failed to load trigger, HTTP code = " + str(res.status_code))
        print("\nPosted triggers ")
    
    print("\n######### " + nsDirName + " Install Completed #############\n")
print("\n######### Content Install Completed #############\n")
