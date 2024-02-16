from load_key import *
from re import sub
from time import sleep
def call_gpt4_api(history, prompt, repeat: int = 1, retries: int = 3):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-1106-preview",
            messages=[{"role": "system", "content": prompt}, *history],
            temperature=1,
            top_p=1,
            n=repeat,
            presence_penalty=0,
            frequency_penalty=0,
        )
    except Exception as e:
        print(e)
        if retries==0:
            pass
        sleep(2**4-retries)
        return call_gpt4_api(history, prompt, repeat, retries-1)
    print(history)
    return response["choices"]

def call_chatgpt_api(history, prompt, repeat: int = 1, retries: int = 3):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": prompt}, *history],
            temperature=1,
            top_p=1,
            n=repeat,
            presence_penalty=0,
            frequency_penalty=0,
        )
    except Exception as e:
        print(e)
        if retries==0:
            pass
        sleep(2**4-retries)
        return call_chatgpt_api(history, prompt, repeat, retries-1)
    return response["choices"]
def call_instructgpt_api(prompt, retries: int =3):
    try:
        res=openai.Completion.create(
                    model="gpt-3.5-turbo-instruct",
                    prompt=prompt,
                    max_tokens=1024,
                    temperature=0.7,
                )
        return res["choices"][0]["text"].strip().strip("\"")
    except Exception as e:
        print(e)
        if retries==0:
            pass
        sleep(2**4-retries)
        return call_instructgpt_api(prompt, retries-1)

def mark_equations(utterance):
    user_prompt="Utterance: He had 7kg+11kg=18kg of bread\nRewrite: He had 7kg+11kg=<<7+11=18>>18kg of bread.\n\nUtterance: John paid $50 x 6 =$300 to the shopkeeper\nRewrite: John paid $50 x 6 =$<<50*6=300>>300 to the shopkeeper\n\nUtterance: <utterance>\nRewrite:"
    history=[{"role":"user","content":user_prompt.replace("<utterance>",utterance)}]
    prompt="Rewrite the user's utterance with all equations/calculations enclosed in <<>>. Do not change anything else or correct any mathematical error:"
    res=call_chatgpt_api(history,prompt)
    return res[0]["message"]["content"]
