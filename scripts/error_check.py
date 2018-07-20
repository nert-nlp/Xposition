import os, re

dir = 'markdown'

Check = re.compile(r"\\section")

for file in os.listdir(dir):
    with open(os.path.join(dir, file), 'r', encoding='utf8') as f:
        # print(file)
        f = f.readlines()
        for i, line in enumerate(f):
            x = Check.search(line)
            if x:
                print(file, line.strip())

