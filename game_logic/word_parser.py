import pathlib

file = open(str(pathlib.Path(__file__).parent) + '/../resources/word_list.txt', "r", encoding="utf-8")
words = []
for line in file:
    words.append(line.strip(",\n"))
