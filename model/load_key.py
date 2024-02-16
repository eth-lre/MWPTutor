import openai
key=""
if key=="":
 raise Exception("Please add your openai key")
openai.api_key = key
