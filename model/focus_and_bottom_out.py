import json
from sys import argv
from utils import *
from gpt_utils import *
calculation_words={"add","subtract","multiply","divide","quotient","product"}
RETRIES=50
def retry():
    global RETRIES
    RETRIES=RETRIES-1
    if RETRIES<0:
        raise Exception("too many retries")
def solve_step(step):
    # seed=sub("<<.*?>>","",step["step"][0])
    seed=step["step"][0]
    history=[]
    print(step["step"][0])
    truth=findall("<<.*?=.*?>>",step["step"][0].replace(",","").replace("$","").replace("£","").replace('%',""))[0].split("=")[1][:-2].strip()
    prompt="Turn the following statement into a question, which starts with \"What\", or \"How much\" or \"How many\" . Do not mention any mathematical operation like 'multiply', 'add', 'subtract', 'divide' etc. in the question. Also make sure that the answer ':"+truth+"' does not appeear:\n"+seed
    flag=False
    while(True):
        ques=call_gpt4_api(history, prompt)
        if truth not in findallnums(ques[0]["message"]["content"]):
            break
        # Special exception when the RHS is contained in the LHS
        if truth in findallnums(findall("<<.*?>>",step["step"][0].replace(",",""))[0].split("=")[0]):
            flag=True
            break
        print(ques[0]["message"]["content"])
        print(truth)
        retry()    
    history.append(ques[0]["message"])
    history.append({"role":"user", "content":"Now answer the above question based on the "})
    ans=call_gpt4_api(history, prompt)[0]["message"]
    history.append(ans)
    if truth in findallnums(ans["content"]):
        # get a pre-bottom out hint
        history.append({"role":"user","content":"Generate a hint to get this answer. The hint should not include the answer itself:"})
        while True:
            hint=call_gpt4_api(history,prompt)[0]["message"]["content"]
            if truth not in findallnums(hint):
                break
            print("hint")
            print(hint)
            print(truth)
            retry()
        step["question"]=ques[0]["message"]["content"]
        step["hint"]=hint
        step["bottom_out"]=ans["content"]
        step["followups"]=[solve_step(x) for x in step["followups"]]
        if flag:
            step["flag"]=True
        return step
    else:
        print("final")
        print(ans["content"])
        print(ques[0]["message"]["content"])
        print(truth)
        retry()
        return solve_step(step)

data=json.load(open(argv[1]))
for src in data:
    RETRIES=50
    src["solutions_gpt4"]=[solve_step(x) for x in src["solutions_gpt4"]]
    json.dump(data,open(argv[2],"w"))