import os, re

os.chdir(r'C:\Users\Austin\Desktop')

file = r'psst2.tex'
dir = r'Xposition\local\Xposition\scripts\tex'

with open(file, 'r', encoding='utf8') as f:
    data = ''.join(f.readlines())
    split = re.split(r'(\\hier[ABCDE]def{|\\(sub)?section{)', data)
    for s in split:
        title = s[:s.find("}")]
        if '\\' in title:
            continue
        print(title)
        if not os.path.exists('tex'):
            os.mkdir('tex')
        with open(os.path.join(dir,title+'.tex'), 'w+', encoding='utf8') as f2:
            f2.write('\\section{'+s)
