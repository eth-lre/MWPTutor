import argparse
import json
import collections
import random

args = argparse.ArgumentParser()
args.add_argument("--start-i", type=int, default=0)
args.add_argument("--end-i", type=int, default=10)
args = args.parse_args()

data = json.load(open("scripts/balanced1050.json", "r"))
data_per_class = collections.defaultdict(list)

for line in data:
    data_per_class[line["type"]].append({
        "sid": line["sid"],
        "model_prediction": line["type"],
        "sentence": line["sentence"]
    })

print({k: len(v) for k,v in data_per_class.items()})

data_queue = []

for model_prediction, values in data_per_class.items():
    data_queue += values[args.start_i:args.end_i]

random.Random(0).shuffle(data_queue)

with open(f"web/queues/{args.start_i:0>3}_{args.end_i:0>3}.jsonl", "w") as f:
    f.write("\n".join([json.dumps(x, ensure_ascii=False) for x in data_queue]))