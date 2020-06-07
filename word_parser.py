file = open("word_list.txt", "r")
words = []
for line in file:
    words.append(line.strip(",\n"))
