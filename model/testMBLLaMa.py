# python test.py config.json question.json [save_file]
from json import load
from sys import argv
from Tutor_LLAMA import MathLlamaTutor
from student_model import get_student_utterance
from load_key import *
from datetime import datetime
student_config=load(open(argv[1]))

data=load(open(argv[2]))
for question in data:
    mathtutor=MathLlamaTutor(question["solutions"],question["error"]) #if "type" in question and question["type"]=="Llama" else MathTutor(question["solutions"],question["incorrect_answer"])

    student_config["question"]=question["question"]
    student_config["incorrect_solution"]=question["error"]
    if student_config["mode"]=="manual":
        print("Manual mode is on. The module will expect the user to input student responses. Leave a responce empty to fall back to instructGPT")
    last=""
    while mathtutor.status!="TERMINATE" and len(mathtutor.history)<60:
        utterance=mathtutor.run(last)
        print("Teacher:",utterance)
        if student_config["mode"]=="manual":
            last=input()
            if last=="":
                last=get_student_utterance(student_config,mathtutor.history)
        else:
            last=get_student_utterance(student_config,mathtutor.history)
            if last=="Conversation Too Long":
                break
        print("Student:",last)

    if len(argv)>3:
        from json import dump
        question["conversation_mathbot_llama"]="\nEOM\n".join([r+":"+s for r,s in mathtutor.history])
        # question["conversation_chatgpt_modelused"]="gpt-4-1106-preview"
        # question["conversation_chatgpt_time"]=str(datetime.now())
        dump(data, open(argv[3],"w"))