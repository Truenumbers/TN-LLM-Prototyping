
import streamlit as st
import sys
import json

import TnLlmTools as tnu

st.set_page_config(
    page_title="TN/C2X Application",
    page_icon="favicon.ico", # Optional: A favicon for the browser tab
    layout="wide"  # Optional: Sets the page layout to wide mode
)


st.image("c2xLogoPEO41-C.png", width=120)
st.markdown("<span style='font-size:28pt; float:left'>TN/C2X COP Analyzer</span>", unsafe_allow_html=True)
    

#import pandas as pd
#import streamlit as st
#from numpy.random import default_rng as rng

#df = pd.DataFrame(
#    rng(0).standard_normal((1000, 2)) / [50, 50] + [37.76, -122.4],
#    columns=["lat", "lon"],
#)

#st.map(df)

nSpace = "llm-test"

tnData = tnu.queryTn(nSpace, "contains(\"himars\") has *", 200, 0)

returnedText = ""
for tn in tnData["truenumbers"]:
    returnedText += tn["trueStatement"] + ", \n"

thePrompt = "Summarize the following data, elaborating on equipment type and geographical context.  State the approximate size of the given grouping of equipment in mautical miles, and list lat/long of assets: " + returnedText

received_data_obj = tnu.chat_cycle(thePrompt)
received_data = json.dumps(received_data_obj)[1:-1]


st.markdown("##Analysis:<p> " + received_data.replace("\\n","<br>").replace("\\u00b0", " deg ") , unsafe_allow_html=True)