from re import search,sub
from ast import parse
from evaluate import load
from gpt_utils import mark_equations
from nltk.tokenize import word_tokenize
from spellchecker import SpellChecker
from nltk.stem import SnowballStemmer

spell = SpellChecker()
stem= SnowballStemmer("english")
utterance_act=["Generic","Focus","Probing","Telling"]
utterance_type=["Hard-coded","GPT(live)","GPT(cached)"]
bertscore=load("bertscore")
# rewriting the findall function because the inbuilt version works strangely
def findall(regex, string):
    res=[]
    cur=search(regex, string)
    while cur:
        res.append(string[cur.span()[0]:cur.span()[1]])
        string=string[cur.span()[1]:]
        cur=search(regex, string)
    return res
#special case with numerical regex built in
def findallnums(string):
    nums= findall(r"[0-9]+(\.[0-9]+)?",string.replace(",",""))
    return extend_floats(nums)
def extend_floats(nums):
    ex=[]
    for n in nums:
        while "." in n and n[-1]=="0":
            n=n[:-1]
            if n[-1]==".":
                n=n[:-1]
            ex.append(n)
    return nums+ex
equation_regex=r"[0-9]+(\.[0-9]+)?\s*([\+x\*/-]\s*[0-9]+(\.[0-9]+)?\s*)+=\s*[0-9]+(\.[0-9]+)?"
wov={
    "One":1,
    "Two":2,
    "Three":3,
    "Four":4,
    "Five":5,
    "Six":6,
    "Seven":7,
    "Eight":8,
    "Nine":9,
    "Ten":10,
    "Eleven":11,
    "Twelve":12,
    "Thirteen":13,
    "One-Half":0.5,
    "Half":0.5,
    "One-Third":"1/3",
    "Third":"1/3",
    "Double":"2 times",
    "Triple":"3 times"
}

unit_sets=[["minutes","seconds","hours"],["days","weeks"],["feet","inches"]]
unit_map={}
for us in unit_sets:
    for unit in us:
        unit_map[unit]=[t for t in us if t!=unit]
def findallnums_match(utterance):
    # Eliminate commas 
    utterance=utterance.replace(",","")
    for k in wov:
        utterance=utterance.replace(k,str(wov[k])).replace(k.lower(),str(wov[k]))
    # if equations exist, limit to RHS of equations only
    equations=findall(equation_regex,utterance)
    if len(equations)>0:
        return extend_floats([get_eq_RHS(p) for p in equations])
    # else return all numbers
    return [x.replace(" ","") for x in findallnums(utterance)]
def get_eq_RHS(equation): 
    return equation.split("=")[1].replace(">","").replace(" ","").replace("%","").replace("$","")
def parse_eq(eq):
    eq=eq.split("=")
    lhs=eq[0]
    rhs=eq[1]
    outputs=int(rhs) if "." not in rhs else float(rhs)
    def get_inputs(binop):
        res=[]
        if 'value' in binop.left._fields:
            res.append(binop.left.value)
        else:
            res+=get_inputs(binop.left)
        if 'value' in binop.right._fields:
            res.append(binop.right.value)
        else:
            res+=get_inputs(binop.right)
        return res
    
    inputs=get_inputs(parse(lhs).body[0].value)
    return inputs, outputs

def parse_all_eq(solution):
    solution=solution.split("\n")[:-1]              # leave out the answer line
    res=[]
    for step in solution:
        cur={"step":step}
        cur["Equations"]=[]
        for x in findall("<<.*?=.*?>>",step):
            cur["Equations"].append(parse_eq(x[2:-2]))
        res.append(cur)
    return res

def read_out_step(LHS):
    LHS=LHS.replace(",","").replace("x","*")
    if "(" in LHS:
        # Need a better handling of this case
        return "Here is a hint. The required calculation is "+LHS
    numbers=findallnums(LHS)
    operators=findall("[+=\\*/-]",LHS)
    if operators==["+"]:
        return "Here is a hint: you need to add "+numbers[0]+ " and "+ numbers[1]+" to get the answer."
    elif operators==["+","+"]:
        return "Here is a hint: you need to add "+numbers[0]+ ", "+numbers[1]+" and "+ numbers[2]+" to get the answer."
    elif operators==["*"]:
        return "Here is a hint: you need to multiply "+numbers[0]+ " and "+ numbers[1]+" to get the answer."
    elif operators==["*","*"]:
        return "Here is a hint: you need to multiply "+numbers[0]+ ", "+numbers[1]+" and "+ numbers[2]+" to get the answer."
    elif operators==["-"]:
        return "Here is a hint: you need to subtract "+numbers[1]+ " from "+ numbers[0]+" to get the answer."
    elif operators==["-","-"]:
        return "Here is a hint: you need to subtract "+numbers[1]+ " and "+numbers[2]+" from "+ numbers[0]+" to get the answer."
    elif operators==["-","+"]:
        return "Here is a hint: you need to subtract "+numbers[1]+ " from the sum of "+numbers[2]+" and "+ numbers[0]+" to get the answer."
    elif operators==["+","-"]:
        return "Here is a hint: you need to subtract "+numbers[2]+ " from the sum of "+numbers[1]+" and "+ numbers[0]+" to get the answer."
    elif operators==["/"]:
        return "Here is a hint: you need to divide "+numbers[0]+ " by "+ numbers[1]+" to get the answer."
    elif operators==["/", "*"]:
        if numbers[0]=="1":
            return "Here is a hint: you need to divide "+numbers[2]+ " by "+ numbers[1]+" to get the answer."
        else:
            return "Here is a hint: you need to divide "+numbers[0]+ " by "+ numbers[1]+" and then multiply the result by "+ numbers[2]+" to get the answer."
    elif operators==["*", "/"]:
        if numbers[1]=="1":
            return "Here is a hint: you need to divide "+numbers[0]+ " by "+ numbers[2]+" to get the answer."
        else:
            return "Here is a hint: you need to divide "+numbers[1]+ " by "+ numbers[2]+" and then multiply the result by "+ numbers[0]+" to get the answer."
    else:
        return "Here is a hint. The required calculation is "+LHS
    
def get_match(utterance, answer):
    return answer.replace(",","") in findall('[0-9]+(\.[0-9]+)?',utterance.replace(",",""))
def all_match(role, conversation, answer):
    count=0
    for utterance in conversation:
        if utterance.strip().strip("\n").startswith(role):
            if get_match(utterance,answer):
                return count
            count+=1
    return 100000
def evaluate(conversation, answer, threshold):
    conversation=conversation.split("\nEOM\n")
    answer=answer.split("\n")[-1].strip()
    student=all_match("Student:",conversation,answer)
    teacher=all_match("Tutor:",conversation,answer)
    return student<threshold,teacher<min(student,threshold)
def spellcheck(word):
    res=spell.correction(word)
    if res:
        return res
    return word
def keyword_match(utterance, keywords):
    keywords=" ".join(spellcheck(k) for k in word_tokenize(keywords.strip())).lower()
    # Special keywords:
    special_matches=bertscore.compute(predictions=["variable","equation"], references=[keywords]*2, model_type="microsoft/deberta-large-mnli")["f1"]
    if special_matches[0]>0.9:
        if " x " in utterance.replace(","," ") or " y " in utterance.replace(","," ") or " z " in utterance.replace(","," "):
            return special_matches[0]
    if special_matches[1]>0.9:
        # Need to redo this to check the exact equation
        if "=" in utterance:
            return special_matches[1]

    split_utterance=[spellcheck(k).lower() for k in word_tokenize(utterance.strip())]

    # Try matching by stemming for individual words
    if " " not in keywords:
        if sum(stem.stem(keywords)==stem.stem(ref) for ref in split_utterance)>0:
            return 1
    lengths=[k for k in range(len(keywords.split())-2,len(keywords.split())-2+3) if k>0]
    samples=sum([list(" ".join(x) for x in zip(*[split_utterance[i:] for i in range(k)])) for k in lengths],[])
    # remove characters with too many or too few characters
    samples=[s for s in samples if (len(s)/len(keywords)>0.66 and len(s)/len(keywords)<1.5)]
    if len(samples)==0:
        return 0
    return max(bertscore.compute(predictions=samples, references=[keywords]*len(samples),model_type="microsoft/deberta-large-mnli")["f1"])

unit_sets=[["minutes","seconds","hours"],["days","weeks"],["feet","inches"]]
unit_map={}
for us in unit_sets:
    for unit in us:
        unit_map[unit]=[t for t in us if t!=unit]
# A safe version of eval
import ast
import operator as op


def eval_expr_tol(expr, default=True):
    try:
        splits=expr.split("==")
        assert(len(splits)==2)
        LHS=eval_expr(splits[0])
        RHS=float(splits[1])
        if RHS==0:
            return abs(LHS)<0.001
        else:
            return abs(LHS-RHS)/RHS<0.01
    except:
        return eval_expr(expr,default)
# supported operators
operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv}

def eval_expr(expr,default=True):
    try:
        return eval_(ast.parse(expr, mode='eval').body)
    except:
        return default

def eval_(node):
    if isinstance(node, ast.Num): # <number>
        return node.n
    elif isinstance(node, ast.BinOp): # <left> <operator> <right>
        return operators[type(node.op)](eval_(node.left), eval_(node.right))
    elif isinstance(node, ast.UnaryOp): # <operator> <operand> e.g., -1
        return operators[type(node.op)](eval_(node.operand))
    elif isinstance(node, ast.Compare): # equality
        if isinstance(node.ops[0],ast.Eq):
            return eval_(node.left)==eval_(node.comparators[0])
        else:
            raise TypeError(node,type(node))
    else:
        raise TypeError(node,type(node))

