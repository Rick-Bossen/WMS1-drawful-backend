import pathlib

file = open(str(pathlib.Path(__file__).parent) + '/../word_list.txt', "r")
words = []
for line in file:
    words.append(line.strip(",\n"))
