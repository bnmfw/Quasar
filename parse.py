import re

def parse(dir: str, filename: str) -> None:
    models = []
    current_model = None
    with open(f"{dir}/{filename}", "r") as file:
        for i, line in enumerate(file):
            if not i or line[0] == "*": continue
            if line[0] == ".":
                tokens = line.split()
                if current_model is not None: models.append(current_model) 
                current_model = {"name": tokens[1], "type": tokens[2], "extra": " ".join(tokens[3:]), "attributes": []}
            if line[0] == "+":
                line = line[1:]
                t = [e for e in re.split(r'[ =\n]', line) if e]
                att = [(t[i], t[i+1]) for i in range(0, len(t), 2)]
                current_model["attributes"].append(att)
    
    with open(f"test.pm", "w") as file:
        tab = "\t\t"
        for model in models:
            file.write(f"\n.model {model['name']} {model['type']} {model['extra']}\n")
            for att in model["attributes"]:
                file.write(f"+{tab.join(f'{at}={v}' for (at, v) in att)}\n")

parse("circuitos/dis","7nm_FF.pm")