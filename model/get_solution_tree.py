from gpt_utils import *
from utils import *
from sys import argv
import json
base_prompt="Given here is a math word problem which can be solved in 2 to 5 steps. We require you to solve it step by step. Each step must contain a single arithmatic calculation clearly marked with <<->>. For example \"Jason finished half of his cookies, so he ate 60/2 = <<60/2=30>>30 cookies\". \n <problem>"
start_prompt="Begin with the first step. Use only 1 sentence to describe the step:"
cont_prompt="Now give the next step in the same format. Use only 1 sentence to describe the step. If the problem has been solved by the current step, add \"QED\" after the step."
def get_tree(problem, answer, max_steps=6):
    history=[{"role":"user","content":start_prompt}]
    prompt=base_prompt.replace("<problem>",problem)
    res=call_gpt4_api(history,prompt,2+max_steps)
    successes=[]
    eq_map={}
    for choice in res:
        # check that there is an equation
        equations=findall("<<.*?>>",choice["message"]["content"])
        equations=[x.replace(",","").replace(" ","") for x in equations]
        if len(equations)==1:
            if eval_expr(equations[0][2:-2].replace("=","==")):
                if equations[0] not in eq_map:
                    if "QED" not in choice["message"]["content"]:
                        new_history=history+[dict(choice["message"])]
                        subres=get_next_step(prompt, new_history, max_steps-1, answer)
                        if len(subres)>0:
                            eq_map[equations[0]]=len(successes)
                            successes.append({"step":[choice["message"]["content"]],"followups":subres})   
                        else:
                            eq_map[equations[0]]=-1                         
                    else:
                        if float(equations[0][2:-2].split("=")[1])==float(answer):
                            eq_map[equations[0]]=len(successes)
                            successes.append({"step":[choice["message"]["content"]],"followups":[]})
                else:
                    if eq_map[equations[0]]>=1:
                        successes[eq_map[equations[0]]]["step"].append(choice["message"]["content"])
    return successes
def get_next_step(prompt, history, max_steps, answer):
    if max_steps==0:
        return []
    history=history+[{"role":"user","content":cont_prompt}]
    res=call_gpt4_api(history,prompt,2+max_steps)
    successes=[]
    eq_map={}
    for choice in res:
        # check that there is an equation
        equations=findall("<<.*?=.*?>>",choice["message"]["content"])
        equations=[x.replace(",","").replace(" ","") for x in equations]
        if len(equations)==1:
            if eval_expr(equations[0][2:-2].replace("=","==")):
                if equations[0] not in eq_map:
                    if "QED" not in choice["message"]["content"]:
                        new_history=history+[dict(choice["message"])]
                        subres=get_next_step(prompt, new_history, max_steps-1, answer)
                        if len(subres)>0:
                            eq_map[equations[0]]=len(successes)
                            successes.append({"step":[choice["message"]["content"]],"followups":subres})   
                        else:
                            eq_map[equations[0]]=-1                         
                    else:
                        if equations[0][2:-2].split("=")[1].isnumeric() and float(equations[0][2:-2].split("=")[1])==float(answer):
                            eq_map[equations[0]]=len(successes)
                            successes.append({"step":[choice["message"]["content"]],"followups":[]})
                else:
                    if eq_map[equations[0]]>=1:
                        successes[eq_map[equations[0]]]["step"].append(choice["message"]["content"])
    return successes
data=json.load(open(argv[1]))
for source in data:
    if "solutions_gpt4" not in source or source ["solutions_gpt4"]==[]:
        res=[]
        for i in range(200):
            res=get_tree(source["question"],source["final_ans"])
            if len(res)>0:
                break
        source["solutions_gpt4"]=res
        json.dump(data,open(argv[2],"w"))