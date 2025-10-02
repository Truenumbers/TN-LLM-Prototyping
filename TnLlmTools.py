##  TN Discovery tools for LLMs

## Return list of returned TNs where subject contains each of a list of terms
import requests
import json
import ollama
import pandas as pd

## TN Tools

tnRest = "http://gov.truenumbers.com/truenumbers-rest-api"


def query_tn(nSpace, theQuery, limit, offset):

    parms = {"numberspace": nSpace, "limit": limit, "offset": offset}
    res = requests.post(
        tnRest + "/v2/numberflow/tnql", params=parms, data={"tnql": theQuery}
    )
    if res.status_code == 200:
        return res.json()
    else:
        return None


# Get phrases
# taxType can be subject, property, tags or value
# NOTE:  "value" returns all kinds of value, must test if type is srd


def get_phrases(nSpace, taxType, theQuery, limit, offset):
    parms = {"numberspace": nSpace, "limit": limit, "offset": offset}
    res = requests.post(
        tnRest + "/v2/taxonomy/distinct",
        params=parms,
        data={"taxonomyType": taxType, "tnql": theQuery},
    )
    if res.status_code == 200:
        return res.json()
    else:
        return None


def add_triple_to_dataframe(
    df, subject_str: str, property_str: str, value
) -> pd.DataFrame:
    """
    Ensures required field exist in the dictionary and adds a new row with the given subject, property, and value.

    Parameters:
    - df (dict): The input dictionary.
    - subject_str (str): The value to insert into the 'subject' column.
    - property_str (str): The name of the column to insert the value into.
    - value: The value to insert into the property column.

    Returns:
    - pd.DataFrame: The updated DataFrame.
    """

    # Step 1: Ensure fixed columns exists
    if "subject" not in df.columns:
        df["subject"] = pd.Series(dtype="object")
    if "color" not in df.columns:
        df["color"] = pd.Series(dtype="object")
    if "marker" not in df.columns:
        df["marker"] = pd.Series(dtype="object")

    # Step 2: Ensure property column exists
    if property_str not in df.columns:
        df[property_str] = pd.Series(dtype="object")

    # Step 3: put value in property column
    if subject_str in df["subject"].values:
        # Update the existing row for this subject
        idx = df.index[df["subject"] == subject_str].tolist()[0]
        print("row ", idx)
        df.at[idx, property_str] = value
    else:
        # Add a new row (handled below)
        columnList = df.columns.tolist()
        dataList = columnList.copy()

        mapIcon = "UNKNOWN"
        if "ship" in subject_str.lower():
            mapIcon = "SHIP"
        if "aircraft" in subject_str.lower():
            mapIcon = "AIRCRAFT"
        if "artillery" in subject_str.lower():
            mapIcon = "ARTILLERY"

        flagColor = "UNKNOWN"
        if " ch " in subject_str.lower():
            flagColor = "China"
        if " us " in subject_str.lower():
            flagColor = "USA"
        if " sw " in subject_str.lower():
            flagColor = "Sweden"

        dataList[columnList.index("subject")] = subject_str
        dataList[columnList.index("color")] = flagColor
        dataList[columnList.index("marker")] = mapIcon
        dataList[columnList.index(property_str)] = value
        newFrame = pd.DataFrame([dataList], columns=columnList)
        df = pd.concat([df, newFrame], ignore_index=True)

    return df


# Make a data frame from a list of TN sentences


def df_from_tns(tnResult):
    df = pd.DataFrame()
    for tnObj in tnResult["truenumbers"]:
        tn = tnObj["trueStatement"]
        parts1 = tn.split(" has ")
        subj = parts1[0].strip()
        parts2 = parts1[1].split("=")
        prop = parts2[0].strip()
        value = parts2[1].strip()
        if tnObj["value"]["type"] == "numeric":
            value = float(tnObj["value"]["magnitude"])
        df = add_triple_to_dataframe(df, subj, prop, value)
    return df


## LLM Tools

## Parameters for endpoints, model and numberspace

llmHost = "http://192.168.40.180:11434"

MODEL = "llama3.1:8b"


def chat_cycle(user_input):
    """
    Main chat cycle that processes user input and handles tool calls.
    """
    messages = [
        {
            "role": "system",
            "content": (
                "You are a Navy command and control operator that can answer questions about the common operational picture. "
                "Your interests are in movement of ships, aircraft and artillery; and protection of US assets from CH assets. "
            ),
        }
    ]

    # Initialize LM Studio client
    client = ollama.Client(host=llmHost)

    messages.append({"role": "user", "content": user_input})
    try:
        response = client.chat(
            model=MODEL, messages=messages, keep_alive=-1, options={"num_ctx": 8192}
        )

        # Handle regular response

        return response.message.content

    except Exception as e:
        print(
            f"\nError chatting with the Ollama server!\n\n"
            f"Please ensure:\n"
            f"1. Ollama server is running \n"
            f"2. Model '{MODEL}' is downloaded\n"
            f"3. Model '{MODEL}' is loaded, or that just-in-time model loading is enabled\n\n"
            f"Error details: {str(e)}\n"
        )
