from os import system

for i in range(12,26):
    with open("input.txt", "w") as file:
        file.write(f"V{i}\n\n\n\n\n\ninSel inA inB\nout\n1\n5")
    system("make < input.txt")