## TN Utilities for Trigger Scripts 2.0

## Start with imports and getting system context

import requests
import json
import time
import os
import sys
import difflib
import hashlib
import base64
import re

## phrase to path
def pathOfPhrase(phrase):
    spacePhrase = re.sub(r"\s+"," ",phrase)
    pList = spacePhrase.split(" ")
    pList.reverse()
    return ":".join(pList).replace(":of:","/").replace(":OF:","/")

## Return list of queried TNs or Null if error
def queryTns(nSpace, theQuery, limit, offset):
    parms = { "numberspace":nSpace,"limit":limit,"offset":offset}
    res = requests.post(tnRest + "/v2/numberflow/tnql", 
                params = parms,
                data = {"tnql":theQuery})
    if res.status_code == 200:
        return res.json()["truenumbers"]
    else:
        return None

## Post tns from one text string of statmenets and return HTTP return code
def postTns(nSpace, tnString):
    if tnString.strip()[0] != "{":
        payload = { "trueStatement" : tnString, "noReturn":True}
    else:
        payload = tnString
    parms = {"numberspace":nSpace}
    res = requests.post(tnRest + "/v2/numberflow/numbers", 
                params = parms, data = payload)
    return res.status_code

## Post tns from one text string with list of tags
def postTaggedTns(nSpace, tnString, tags):
    if tnString.strip()[0] != "{":
        payload = { "trueStatement" : tnString, "noReturn":True, "tags":tags}
    else:
        payload = tnString
    
    parms = {"numberspace":nSpace}
    res = requests.post(tnRest + "/v2/numberflow/numbers", 
                params = parms, data = payload)
    return res.status_code

## DELETE tns matching a query
def deleteTns(nSpace, theQuery):
    parms = { "numberspace":nSpace}
    res = requests.delete(tnRest + "/v2/numberflow/numbers", 
                params = parms,
                json = {"tnql":theQuery})
    return res.status_code

## get date string from epoch time
def dtgDate(dtgNum):
    tx = dtgNum
    if tx > 1e11:
        tx = tx // 1000
    time1 =  time.gmtime(tx)
    return time.strftime("%Y-%m-%dT%H:%M", time1)
    
## Find best match for a string from a list of candidates ##
##  Returns dict with matching string, its index, and its score (1.0 is perfect match)
##  Returns None if scores below 0.25

def bestMatch(inputString, candidateList):
    inputUpper = inputString.upper().replace("_"," ")
    if len(inputUpper) < 4:
        return None
    score = 0
    matchIndex = -1
    currentBest = ""
    index = 0
    for candidate in candidateList:
        if candidate.endswith(" " + inputUpper):
            newScore = 0.9
        elif candidate == inputUpper.strip():
            newScore = 1.0
        else:
            matcher = difflib.SequenceMatcher(None, inputUpper, candidate)
            newScore = matcher.ratio()
        if newScore > score:
            score = newScore
            currentBest = candidate
            matchIndex = index
        index = index + 1
    if score > 0.25:
        return {"match":currentBest, "index":matchIndex,"score":score}
    else:
        return None

## Get artifact with a query to the artifact numberspace

def getArtifactByQuery(nSpace, theQuery):
    res = requests.post(tnRest + "/v2/numberflow/tnql", 
    params =  { "numberspace":nSpace},
    data = {"tnql":theQuery})
    returnedTns = res.json()["truenumbers"]
    if res.status_code == 200:
        if len(returnedTns) > 0:
            fileGuid = res.json()["truenumbers"][0]["value"]["value"]
            fileRes = requests.get(tnArtifact + "/v1/artifact/" + fileGuid)
            if fileRes.status_code == 200:
                return fileRes.text
    return None

## Get artifact by Id
def getArtifact(fileId, isText):
    fileRes = requests.get(tnArtifact + "/v1/artifact/" + fileId)
    if fileRes.status_code == 200:
        if isText:
            return fileRes.text
        else:
            return fileRes.content
    else:
        return None

## DELETE artifact by id
## Get artifact by Id
def deleteArtifact(fileId):
    fileRes = requests.delete(tnArtifact + "/v1/artifact/" + fileId)
    if fileRes.status_code == 200:
        return fileRes.text
    else:
        return None

## Put artifact as TN from string data
def putArtifactTnFromString(fName, stringData, artifactId):
    in_memory_file = io.StringIO(stringData)
    in_memory_file.name = fName
    maybeId = ""
    if artifactId != "":
        maybeId = "/" + artifactId
    res = requests.post(tnArtifact + "/v1/artifact" + maybeId,  files={"artifact":in_memory_file})
    return res.json()["artifact"]

