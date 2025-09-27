##  TN Discovery tools for LLMs

## Return list of returned TNs where subject contains each of a list of terms
import requests
import json
import ollama

## TN Tools

tnRest = "http://gov.truenumbers.com/truenumbers-rest-api"


def queryTn(nSpace, theQuery, limit, offset):
    
    parms = { "numberspace":nSpace,"limit":limit,"offset":offset}
    res = requests.post(tnRest + "/v2/numberflow/tnql", 
                params = parms,
                data = {"tnql":theQuery})
    if res.status_code == 200:
        return res.json()
    else:
        return None

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

    messages.append({"role": "user", "content": user_input })
    try:
        response = client.chat(
            model=MODEL,
            messages=messages,
            keep_alive=-1,
            options={'num_ctx': 8192}
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
    
