import json

arq: str = "c17v4"

def mapper(codigo: str) -> list:
    if codigo == "rr": return ["rise", "rise"]
    if codigo == "rf": return ["rise", "fall"]
    if codigo == "fr": return ["fall", "rise"]
    if codigo == "ff": return ["fall", "fall"]

reg: dict = json.load(open(f"circuitos/{arq}/{arq}.json", "r"))
for nodo in reg["nodos"]:
    nodo["critico"]["orie"] = mapper(nodo["critico"]["orie"])
    for let in nodo["lets"]:
        let["orie"] = mapper(let["orie"])

json.dump(reg, open(f"circuitos/{arq}/{arq}.json", "w"))