import os, re

dir = 'markdown-and-macros'

Check = re.compile(r"\[\[")

for file in os.listdir(dir):
    if os.path.isdir(os.path.join(dir, file)):
        continue
    with open(os.path.join(dir, file), 'r', encoding='utf8') as f:
        f = f.readlines()
        for i, line in enumerate(f):
            x = Check.search(line)
            if x:
                print(file, line.strip())

