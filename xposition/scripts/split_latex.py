import os, re

file = 'latex.tex'
dir = 'tex-test'

with open(file, 'r', encoding='utf8') as f:
    data = ''.join(f.readlines())
    split = re.split(r'(\\hier[ABCDE]def{|\\section{|\\subsection{)', data)
    print(len(split))
    for s in split:
        title = s[:s.find("}")].replace('?','').replace('/','')
        title = title.replace('\\backi', '`i').replace('\\backd', '`d')
        title = title.replace('\\backc', '`c').replace('\\backposs', '`$')
        if '\\' in title:
            continue
        print(title)
        if not os.path.exists(dir):
            os.mkdir(dir)
        with open(os.path.join(dir,title+'.tex'), 'w+', encoding='utf8') as f2:
            f2.write('\\section{'+s)
