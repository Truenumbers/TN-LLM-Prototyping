import json
from jsonpath_ng import jsonpath, parse
import re

##################### classes for transforming JSON msgs to TN ##########################
#
# Methods for parsing JSON, and for writing TNs are packaged in static class TnUtility
#


class TnUtility:

    ## TN generator: generate TNs from the JSON input and a few parameters
    #
    # Params:
    #  jsonMsg - the json object to translate
    #  subjectAll - string to use as subject in all generated tns
    #  parts - dict where keys are JSON field names, and values are a suffix for subjectAll, to be used at that field and below
    #          if the value doesn't start with a : or / it will be used as the subject by itself
    #  tagAlls - array of tags to be applied to all generated tns
    #  swaps - dict where keys are existing JSON field names, to be replaced by the value: {"lat" : "latitude"}
    #  drops - array of JSON field names to be omitted from translation
    #  noQuotes - array of JSON field names who's values should NOT be quoted (they are by default)

    @staticmethod
    def JSON2TN(
        jsonmsg,
        subjectAll,
        parts,
        tagAlls,
        swaps,
        drops,
        noQuotes,
        tokenizer,
        doPaths,
        breakCamels,
    ):
        accumTns = []  # accumulate list of TNs for output

        # Function for recursive descent through input JSON
        # thePath - List of names from the json name/value pairs accumulated recursively
        # subMsg - json subtree being recursed on

        def writeStructTns(thePath, subMsg, theSubj):
            ## Handle an object
            if type(subMsg) is dict:
                for (
                    slotKey,
                    slotValue,
                ) in subMsg.items():  # loop through each slot in the message
                    improvedSlotKey = slotKey
                    localPath = thePath.copy()  # clone passed in name path
                    if slotKey not in drops:  # don't recurse if in the drop list
                        if slotKey in swaps.keys():
                            improvedSlotKey = swaps[slotKey]
                        if slotKey in parts.keys():
                            thePart = parts[slotKey]
                            if thePart.startswith(":") or thePart.startswith("/"):
                                theSubj += thePart
                            else:
                                theSubj = thePart
                        if tokenizer is None:
                            improvedSlotKey = TnUtility.clean(improvedSlotKey)
                        else:
                            improvedSlotKey = tokenizer(improvedSlotKey)
                        localPath.append(improvedSlotKey)
                        writeStructTns(
                            localPath, slotValue, theSubj
                        )  # recurse into value object

            ## Handle a list
            elif type(subMsg) is list:
                countNum = 1
                for element in subMsg:
                    localPath = thePath.copy()
                    # localPath.append("--" + str(countNum))
                    lastTerm = localPath[-1] + "-" + str(countNum)
                    localPath.append(lastTerm)
                    countNum += 1
                    writeStructTns(
                        localPath, element, theSubj
                    )  # recurse into each element of array
                    localPath.pop()

            ## Handle leaf node, write the TN
            else:
                slotValue = str(subMsg)
                if thePath[-1] not in noQuotes:
                    slotValue = '"' + str(subMsg) + '"'
                theTn = TnUtility.makeTn(thePath, slotValue, theSubj, tagAlls, doPaths)
                accumTns.append(theTn)

        ##############
        # Top-level function code here
        initialEnvironment = []
        accumTns = []  ## empty list of generated TNs

        writeStructTns(
            initialEnvironment, jsonmsg, subjectAll
        )  # start recursive descent

        returnStr = ";\n".join(accumTns)
        return returnStr

    # Make the TN for leaf node in the json

    @staticmethod
    def makeTn(env, val, subjPhrase, theTags, doPaths):
        envList = env
        if doPaths:
            propPhrase = " ".join(env)  # make path phrase as TN property
        else:
            propPhrase = env[-1]
            theTags.append(" ".join(env))
        theTn = subjPhrase + " has "
        if len(theTags) == 0:
            tagStr = ""
        else:
            tagStr = "  (" + ",".join(theTags) + ")"
        theTn += propPhrase + " = " + str(val) + tagStr
        # theTn = theTn.replace("--","item-")
        # print(theTn)
        theTags.pop()
        return theTn

    # make a phrase from camelcase or underscored token
    @staticmethod
    def camel2phrase(tok):
        new_string = ""
        s = tok.replace("_", "*").strip()  #
        if len(s) > 3:
            if s[0].isupper() and s[1].islower():
                s = s[0].lower() + s[1:]
        lastIsLower = False
        for i in s:
            if i.isupper() and lastIsLower:
                new_string += "*" + i.lower()
            else:
                new_string += i
            lastIsLower = i.islower()
        x = new_string.split("*")
        return " ".join(x)

    # make a path from camelcase or underscored token
    @staticmethod
    def camel2path(tok):
        new_string = ""
        s = tok.replace("_", "*").strip()  #
        if len(s) > 3:
            if s[0].isupper() and s[1].islower():
                s = s[0].lower() + s[1:]
        lastIsLower = False
        for i in s:
            if i.isupper() and lastIsLower:
                new_string += "*" + i.lower()
            else:
                new_string += i
            lastIsLower = i.islower()
        x = new_string.split("*")
        return ":".join(reversed(x))

    @staticmethod
    def trimCommonStart(pathList):
        prevPath = ""
        returnList = []
        for path in pathList:
            if path.startswith(prevPath):
                path = path[len(prevPath) :]
                if len(path) > 3:
                    if (path[0] == "s") and path[1].isupper():
                        path = path[1:]
            prevPath = path
            returnList.append(path)
        return returnList

    @staticmethod
    # clean a string to be a token
    def clean(strng):
        noSpaces = strng.replace(" ", "_")
        return re.sub("[^a-zA-Z0-9-_]", "", noSpaces)

    @staticmethod
    # expand a path into a phrase
    def phrasify(path):
        phrase = ""  # initial phrase
        hasaList = path.split("/")
        for seg in reversed(hasaList):
            isaList = seg.split(":")
            ##isaList = TnUtility.trimCommonStart(isaList) ## remove redundant prefixes endmic in json
            isaPhrase = ""
            for term in reversed(isaList):
                isaPhrase += TnUtility.camel2phrase(term).strip() + " "
            if len(phrase) > 0:
                phrase += " of " + isaPhrase.strip() + " "
            else:
                phrase = isaPhrase.strip() + " "
        return phrase.replace("  ", " ")

    @staticmethod
    # Convert JSON to TNs using sentence templates
    def TNS_FROM_JSON(jsonmsg, templates):
        accumTns = []  # accumulate list of TNs for output

        # templates parameter is a list of sentence strings for substitution


######################### end of classes for transforming JSON msgs to TN ############################
