import os, re


os.chdir(r'C:\Users\Austin\Desktop\Xposition\local\Xposition\scripts')

dir = 'markdown-and-macros'

Check = re.compile(r"<u>.*</u>")

for file in os.listdir(dir):
    with open(os.path.join(dir, file), 'r', encoding='utf8') as f:
        # print(file)
        f = f.readlines()
        for i, line in enumerate(f):
            x = Check.search(line)
            if len(re.findall('en/as',line))>1:
                print(file, line.strip())

