import openai
from time import sleep
student_prompt="Student Persona: (STUDENT PERSONA)\n\n Math problem: (MATH PROBLEM)\n\n Student solution: (STUDENT SOLUTION)\n\n Context: (STUDENT NAME) thinks their answer is correct. Only when the teacher provides several good reasoning questions, (STUDENT NAME) understands the problem and corrects the solution. (STUDENT NAME) can use calculator and thus makes no calculation errors. Send EOM tag at end of the student message.\n\n (DIALOG HISTORY).\nStudent:"
def get_student_utterance(config,history):
    hs=history
    history="<EOM>\n\n".join([s+": "+h for s,h in history])
    prompt=student_prompt.replace("(STUDENT PERSONA)",config["student_persona"]).replace("(STUDENT SOLUTION)",config["incorrect_solution"]).replace("(MATH PROBLEM)",config["question"]).replace("(STUDENT NAME)",config["student_name"]).replace("(DIALOG HISTORY)",history)
    # print(prompt)
    if len(prompt.split(" "))>2000:
        return "Conversation Too Long"
    result=""
    retries=0
    empties=0
    last_fail=False
    while(len(result)<5 and empties<3):
        if retries>0 and last_fail:
            print("sleeping for",min(64,2**retries),"seconds")
            sleep(min(64,2**retries))
        try:
            last_fail=True
            res=openai.Completion.create(
                model="gpt-3.5-turbo-instruct",
                prompt=prompt,
                max_tokens=1024,
                temperature=0.4,
                stop=["Teacher:","Tutor:"],
            )
#             response = openai.ChatCompletion.create(
#                 model="gpt-3.5-turbo",
#                 messages=[{"role": "system", "content": prompt}, *history],
#                 temperature=0.4,
#                 top_p=1,
#                 n=repeat,
#                 presence_penalty=0,
#                 frequency_penalty=0,
#             )
            result=res["choices"][0]["text"].strip().strip("\"")
            empties+=1
#             if len(result)<5 and "goodbye" not in hs[-2][1].lower()+hs[-4][1].lower():
#                 print("Empty student reponse")
#                 print(history)
#             elif len(result)<5 and "goodbye" in hs[-2][1].lower()+hs[-4][1].lower():
#                 break
        except Exception as e:
            print(e)
            retries+=1
            last_fail=False
        utterance=result.replace("Student:","").replace(config["student_name"]+":","").replace("<EOM>","").strip("\n")
        return utterance