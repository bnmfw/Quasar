import os

modules = ["matematica", "graph", "concorrencia", "spiceInterface", "circuito", "letFinder", "circuitManager", "mcManager"]

print("Testing Quasar...")
for module in modules:
    os.system(f"python3 -m utils.{module}")
print("Quasar OK")
