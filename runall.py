from os import system
for circ in ["nor6","nand6"]:
    with open("input.txt", "w") as file:
        file.write(f"{circ}\n\na b c d e f\ng1\n2\n\n3")
    system("make < input.txt")