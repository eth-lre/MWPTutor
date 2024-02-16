
from gpt_utils import *
from utils import *
class Tutor:
    def __init__(self):
        self.sequence=[]
        self.status="INIT"
        self.checks=[]
        self.solution_node=None
        self.history=[]
        self.last_utterance=""
        self.next_utterance=""
        self.metadata={}
    def start_conversation(self):
        raise NotImplementedError()
    def run_conversation(self):
        raise NotImplementedError()
    def run(self, last_utterance):
        self.last_utterance=last_utterance
        if self.status=="INIT":
            self.start_conversation()
        elif self.status!="TERMINATE":
            self.history.append(("Student",last_utterance))
            self.run_conversation()
        else:
            return "The Tutor has Ended this conversation"
        self.history.append(("Tutor",self.next_utterance))
        return self.next_utterance

teacher_base="""A tutor and a student work together to solve the following math word problem. 
Math problem: {problem}
The correct answer is as follows:{answer}
You need to role-play the tutor while the user roleplays the student, Kayla. The tutor is a soft-spoken empathetic man who dislikes giving out direct answers to students, and instead likes to answer questions with other questions that would help the student understand the concepts, so that she can solve the problem themselves. 
Kayla has come up with a solution, but it is incorrect. Please start the conversation, one line at a time, aiming to figure out what is Kayla's solution and what is wrong with it. Then try to get her to fix it. Write 'goodbye' if you are done with the conversation
"""
class ChatGPTTutor(Tutor):
    def __init__(self,problem,correct_answer):
        super().__init__()
        self.prompt=teacher_base.format(problem=problem,answer=correct_answer)
    def start_conversation(self):
        self.status="CONT"
        self.next_utterance="Hi! Could you walk me through your solution?"
    def run_conversation(self):
        history=[{"role":"assistant" if s=="Tutor" else "user","content":m} for s,m in self.history]
        res=call_chatgpt_api(history,self.prompt)
        self.next_utterance=res[0]["message"]["content"]
        if "goodbye" in self.next_utterance.lower() or len(self.next_utterance)<2:
            self.status="TERMINATE"
class GPT4Tutor(Tutor):
    def __init__(self,problem,correct_answer):
        super().__init__()
        self.prompt=teacher_base.format(problem=problem,answer=correct_answer)
    def start_conversation(self):
        self.status="CONT"
        self.next_utterance="Hi! Could you walk me through your solution?"
    def run_conversation(self):
        history=[{"role":"assistant" if s=="Tutor" else "user","content":m} for s,m in self.history]
        res=call_gpt4_api(history,self.prompt)
        self.next_utterance=res[0]["message"]["content"]
        if "goodbye" in self.next_utterance.lower() or len(self.next_utterance)<2:
            self.status="TERMINATE"
class MathTutor(Tutor):
    def __init__(self,solution_node,student_solution):
        super().__init__()
        self.checks=[]
        self.aligned_steps=[]
        self.align_threshold=0.9
        self.seek_threshold=0.85
        self.metadata["solution"]=student_solution
        self.solution_node=solution_node
        self.full_sol=[]
    def align_solution(self, student_solution, cur_step=0):
        if type(student_solution) is not list:
            student_solution=student_solution.split("\n")[:-1]
        if len(student_solution)==cur_step:
            return False
        student_step=mark_equations(student_solution[cur_step]) 
        best_node=None
        best_score=-1
        for followup in self.solution_node:
            scores=bertscore.compute(predictions=[sub("<<.*?=.*?>>","",x) for x in followup["step"]],references=[sub("<<.*?=.*?>>","",student_step) for _ in followup["step"]],lang="en")["f1"]
            if max(scores)>self.align_threshold:
                #check if equation rhs appears in the step
                RHS=get_eq_RHS(findall("<<.+?=.+?>>",followup["step"][0])[0])
                if RHS in findallnums_match(student_step):
                    if max(scores)>best_score:
                        best_score=max(scores)
                        best_node=followup
            if best_score>0:
                self.aligned_steps.append(followup["step"][0])
                self.full_sol.append(followup["step"][0])
                self.solution_node=best_node["followups"]
                return self.align_solution(student_solution,cur_step+1)
            else: 
                return True
    def check_correct(self, no_convert=False):
        RHS=get_eq_RHS(findall("<<.*?=.*?>>",self.solution_node["step"][0])[0]).replace(",","")
        if RHS in findallnums_match(self.last_utterance):
            # proceed to the next step
            self.full_sol.append(self.solution_node["step"][0])
            self.solution_node=self.solution_node["followups"]
            if len(self.solution_node)>0:
                self.status="SEEK"
                self.next_utterance=RHS+" is correct, well done. What is the next step?"
            else:
                self.status="TERMINATE"
                self.next_utterance=RHS+" is the correct answer to the problem. Well done!!! Don't hesitate to contack me again if you have any troubles."
            return True
        if not no_convert and "Can you convert the answer" not in self.next_utterance:
            for u in unit_map:
                if u in self.last_utterance.lower():
                    for t in unit_map[u]:
                        if t in " ".join(self.solution_node["step"]):
                            self.next_utterance="Can you convert the answer to "+t+" instead of "+u+"?"
                            return True
        
        print([RHS],findallnums_match(self.last_utterance))
        return False
    def start_conversation(self):
        if not self.align_solution(self.metadata["solution"]):
            self.status="TERMINATE"
            self.next_utterance="That is the correct answer. Good job on solving the question!"
        if len(self.aligned_steps)==0:
            self.status="FRESH"
            self.next_utterance="I see your solution. You seem to have made some errors. How about we start fresh and do it step by step?"
        else:
            self.status="SEEK"
            self.next_utterance="You are correct upto where you say \""+self.aligned_steps[-1]+"\". What do you think should be the next step?"
    def run_conversation(self):
        self.check_equations()
        match self.status:
            case "FRESH":
                self.fresh()
            case "SEEK":
                self.seek()
            case "FOCUS":
                self.focus()
            case "PUMP"|"CALCULATE":
                self.pump()
            case "HINT":
                self.hint()
            case "TELLING":
                self.telling()
            case "EQ_FIX":
                self.eq_fix()
            case "EQ_CHECK":
                self.eq_check()
            case "PROB":
                self.prob()
            case "PROB_FAIL":
                self.prob_failure()
            case _:
                raise NotImplementedError("Status "+self.status+" is not implemented")
    def fresh(self):
        # check to see if student has already given out the first step
        original_solution_node=self.solution_node
        for followup in original_solution_node:
            self.solution_node=followup
            if self.check_correct():
                return
        self.solution_node=original_solution_node
        self.status="SEEK"
        self.next_utterance="What should be the first step?"
    def seek_broken(self):
        #Try to identify what next step is most aligned with the next student step
        best_node=None
        best_score=-1
        for followup in self.solution_node:
            scores=bertscore.compute(predictions=[sub("<<.*?=.*?>>","",x) for x in followup["step"]],references=[self.last_utterance for _ in followup["step"]],lang="en")["f1"]
            if max(scores)>best_score:
                best_score=max(scores)
                best_node=followup
        self.solution_node=best_node
        if best_score<self.seek_threshold:
            self.status="PUMP"
            self.next_utterance="Tell me this instead:"+self.solution_node["question"]
        else:
            # make a quick check to see if the student has already answered the question
            RHS=get_eq_RHS(findall("<<.*?=.*?>>",self.solution_node["step"][0])[0])
            if not self.check_correct():
                # ask for answer
                self.status="FOCUS"
                self.next_utterance="Okay, can you do that calculation?"
    def seek(self):
        # the bertscore based alignment method does not work because it is rather finniky
        # Instead, we only accept a step proposed by the student iff all operands are present

        # First check for RHS Match
        original_solution_node=self.solution_node
        print(original_solution_node)
        for followup in original_solution_node:
            self.solution_node=followup
            if self.check_correct(no_convert=True):
                return
        # next check for LHS Match
        values=set(findallnums(self.last_utterance))
        for followup in original_solution_node:
            LHS=findallnums(findall("<<.*?=.*?>>",followup["step"][0])[0][2:-2].split("=")[0])
            lhs=set(LHS)
            #only ask for calculation is "=" is not present already
            if lhs.issubset(values) and "=" not in self.last_utterance:
                self.status="FOCUS"
                self.next_utterance="Okay, can you do that calculation?"
                return
        self.solution_node=original_solution_node[0]
        self.status="PUMP"
        self.next_utterance="Tell me this instead:"+self.solution_node["question"]

            

    def focus(self):
        # check to see if student got answer right. If not, proceed to PUMP
        if not self.check_correct():
            self.status="PUMP"
            self.next_utterance="Let us try again: "+self.solution_node["question"]
    def pump(self):
        if not self.check_correct():
            # Check if there are equations
            equations=findall("<<.*?=.*?>>",mark_equations(self.last_utterance))
            if len(equations)==0 and self.status!="CALCULATE":
                self.status="CALCULATE"
                self.next_utterance="Can you show me your calcuations?"
            else:
                if "problematize" in self.solution_node and "ERROR" not in self.solution_node["problematize"][0] and ("probing" not in self.metadata or self.metadata["probing"]==False):
                    self.status="PROB"
                    self.next_utterance="Let us try a different scenario. " + self.solution_node["problematize"][0]
                    self.metadata["probing"]=True
                    return
                self.metadata["probing"]=False
                self.status="HINT"
                self.next_utterance="That is not quite right. Here is a Hint: "+self.solution_node["hint"]
    def prob(self):
        LHSRHS=self.solution_node["problematize"][1].split("=")
        LHS=LHSRHS[0]
        RHS=LHSRHS[1]
        if RHS in findallnums_match(self.last_utterance):
            self.status="PUMP"
            self.next_utterance="Good job. Now apply the same idea to the previous question:"+self.solution_node["question"]
        else:
            self.status="PROB_FAIL"
            self.next_utterance=read_out_step(LHS)
    def prob_failure(self):
        RHS=self.solution_node["problematize"][1].split("=")[1]
        if RHS in findallnums_match(self.last_utterance):
            self.next_utterance="Good Job. Now apply the same idea to the previous question:"+self.solution_node["question"]
        else:
            self.next_utterance="Nevermind, lets just focus on the previous question:"+self.solution_node["question"]
        self.status="PUMP"
    def hint(self):
        if not self.check_correct():
            self.status="TELLING"
            self.next_utterance="That is still not right. "+self.solution_node["bottom_out"]+" Can you see that."
    def telling(self):
        if not self.check_correct():
            RHS=get_eq_RHS(findall("<<.*?=.*?>>",self.solution_node["step"][0])[0])
            self.next_utterance="The correct answer is "+RHS+" Please say that back to me."
    def check_equations(self):
        equations=findall("<<.*?=.*?>>", mark_equations(self.last_utterance))
        self.metadata["errors"]=[x[2:-2] for x in equations if not eval_expr_tol(x[2:-2])]
        if len(self.metadata["errors"])>0:
            self.metadata["last_status"]=self.status
            self.status="EQ_FIX"
    def eq_fix(self):
        eq=self.metadata["errors"][0]
        self.last_utterance="Can you tell me what is "+eq.split("=")[0]
        self.status="EQ_CHECK"
    def eq_check(self):
        eq=self.metadata["errors"][0]
        LHS=eq.split("=")[0]+"="
        candidates=findallnums_match(self.last_utterance)
        if any(eval_expr_tol(LHS+n,False) for n in candidates):
            del self.metadata["errors"][0]
            if len(self.metadata["errors"])>0:
                self.eq_fix()
                truth=str(eval_expr(LHS[:-1]))
                self.last_utterance="That is right, "+LHS+truth+". "+self.last_utterance
            else:
                self.last_utterance="That is right, "+LHS+truth+". Now answer the earlier question keeping this in mind"
                self.status=self.metadata["last_status"]
# class BioTutor()


        
