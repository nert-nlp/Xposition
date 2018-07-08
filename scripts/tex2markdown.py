#coding=utf-8

"""
This code is for importing our Preposition Supersense v2 guidelines
into our new Xposition website/wiki
3/21/18 Austin Blodgett
"""
import re, os
# import django
# os.chdir('..\scripts')

dir1 = 'tex'
dir2 = 'markdown'


# example_index = 1

def replace_circumfix(s, prefix, repl_prefix, repl_suffix):
    m = re.search(prefix,s)
    start_index = m.end()
    contents = ''
    i=0
    count = 1
    while True:
       c = s[start_index+i]
       if c=='{':
           count += 1
       elif c=='}':
           count -= 1
       if count == 0:
           break
       contents += c
       i+=1
    s1 = s[:m.start()]
    s2 = repl_prefix + contents + repl_suffix
    s3 = s[start_index+i+1:]
    return s1 + s2 + s3

def replace_circumfixes(s, prefix, repl_prefix, repl_suffix):
    while re.search(prefix,s):
        s = replace_circumfix(s, prefix, repl_prefix, repl_suffix)
    return s

def handle_ex(s):
    # global example_index
    s = re.sub(r",(\s)(\s)+", ", ", s, re.MULTILINE)
    s = re.sub(r"(?<=[a-z])(\s+)(?=[a-z])", " ", s, re.MULTILINE)
    s = re.sub(r"(?<=\S)([ \t]*)\\ex", "\n\ex", s)
    s = re.sub(r'\\ex(?=\\)', r'\ex ', s)
    s = re.sub(r'\\ex\t', '\ex ', s)
    s = re.sub(r'\\sn(?=\\)', r'\sn ', s)
    s = re.sub(r'\\sn\t', '\sn ', s)


    match = re.compile(r'\\ex(?=\W)')
    while match.search(s):
        m = match.search(s)
        if s[m.end()]=='{':
            s = replace_circumfix(s, r'\\ex{', '<ex>', '</ex>')
        else:
            start = m.end()
            x = re.compile(r'(\\(ex|sn)|\\end)').search(s, pos=start)
            x = x or re.compile(r'\n').search(s, pos=start)
            end = x.start()

            content = '<ex>' + s[start:end].strip().replace('\n',' ') + '</ex>'
            s = s[:m.start()]+content+'\n'+s[end:]

    match = re.compile(r'\\sn(?=\W)')
    while match.search(s):
        m = match.search(s)
        if s[m.end()] == '{':
            s = replace_circumfix(s, r'\\sn{', '<sn>', '</sn>')
        else:
            start = m.end()
            x = re.compile(r'(\\(ex|sn)|\\end|<ex>)').search(s, pos=start)
            x = x or re.compile(r'\n').search(s, pos=start)
            end = x.start()
            content = '<sn>' + s[start:end].strip().replace('\n', ' ') + '</sn>'
            s = s[:m.start()] + content + '\n' + s[end:]

    return s


def convert(ifile, ofile, title):
    list_num = 1
    footnotes = []

    with open(ifile, 'r', encoding='utf8') as f:
        f = f.readlines()

        # handle junk line by line
        for i, line in enumerate(f):
            if line.strip().startswith('%'):
                 f[i] = ''
            if '\multicolsep' in f[i]:
                f[i] = ''
            if '\\noindent' in f[i]:
                f[i] = re.sub(r'\\noindent', '', f[i])
            # if r'{xlist}' in f[i]:
            #     f[i] = re.sub(r'\\begin{xlist}', '', f[i])
            #     f[i] = re.sub(r'\\end{xlist}', '', f[i])
            # latex comments
            if re.search(r'(?<=[^\\])%', f[i]):
                f[i] = f[i][:re.search(r'(?<=[^\\])%', f[i]).start()]
            # if f[i].strip() == '\ex':
            #     f[i] = ''
            # if re.search(r'\\ex(?=[^\w{])',f[i]):
            #     f[i] = f[i].replace('\ex','<ex>').strip()+'</ex>'
            # take care of [] brackets
            f[i] = re.sub(r'\[\[', r'\[', f[i])
            f[i] = re.sub(r'\][\s\]]', r'\]', f[i])
            # junk whitespace
            f[i] = re.sub(r'\r', r'', f[i])
            f[i] = f[i].strip()+'\n'
            # add numbered list
            if r'\begin{itemize}' in f[i] or r'\begin{enumerate}' in f[i]:
                list_num = 1
            if r'\item' in f[i]:
                f[i] = f[i].replace(r'\item', '###' + str(list_num) + '.')
                list_num += 1



        data = ''.join(f[1:])

        # handle shortdef
        data = replace_circumfixes(data, r'\\shortdef{', r'|', '|')

        # subsection
        data = replace_circumfixes(data, r'\\subsection{', '##<b>', '</b>')

        # embold title of article
        data = re.sub(r'\\psst{' + title + '}', '**' + title + '**', data)

        # handle \p{}
        data = replace_circumfixes(data, r'\\p{', ' [[en/', ']] ')
        # handle \p*{}{}
        data = replace_circumfixes(data, r'\\p\*{', '\\p1{', '](/en/\\p2')
        data = replace_circumfixes(data, r'\\p2{', '', '}')
        data = replace_circumfixes(data, r'\\p1{', ' [', ') ')
        # handle \psst{}
        data = replace_circumfixes(data, r'\\psst{', ' [[', ']] ')
        # handle \rf{}{}
        data = replace_circumfixes(data, r'\\rf{', '\\rf1{', '--\\rf2')
        data = replace_circumfixes(data, r'\\rf2{', '', '}')
        data = replace_circumfixes(data, r'\\rf1{', ' [[', ']] ')
        # reformat links
        while re.search(r' \[\[(.*?)\]\] ', data):
            ref = re.search(r' \[\[(.*?)\]\] ', data).group(1)
            data = data.replace(' [[' + ref + ']] ', '[' + ref + '](/' + ref + ')')
        data = re.sub(r'\[en/', '[', data)
        data = replace_circumfixes(data, r'\\label{', '<label>', '</label>')

        # special characters
        data = data.replace(r'\backi', '[[`i]]')
        data = data.replace(r'\backc', '[[`c]]')
        data = data.replace(r'\backd', '[[`d]]')
        data = data.replace(r'\backposs', '[[`$]]')

        # handle paragraph
        data = replace_circumfixes(data, r'\\paragraph{', '- **', '**')

        # handle bold, italics, quotes
        data = replace_circumfixes(data, r'\\textbf{', '**', '**')
        data = replace_circumfixes(data, r'\\textit{', '<i>', '</i>')
        data = replace_circumfixes(data, r'\\w{', '<i>', '</i>')
        data = replace_circumfixes(data, r'\\emph{', '<i>', '</i>')
        data = replace_circumfixes(data, r'\\uline{', '<u>', '</u>')
        data = replace_circumfixes(data, r'\\texttt{', '`', '`')

        data = re.sub(r'``',"“", data)
        data = re.sub(r'`', "‘", data)
        data = re.sub(r"''", "”", data)
        data = re.sub(r"'", "’", data)
        data = re.sub(r"---", "—", data)
        data = re.sub(r"[.]\\ ", ". ", data)    # e.g. "etc.\ " in LaTeX within a sentence to ensure it is followed by a normal-size space

        # math
        data = re.sub(r"~~", " ", data)
        data = re.sub(r"~", " ", data)
        data = re.sub(r"\\slash ", r"/", data)
        # data = re.sub(r"(?<=[A-Za-z])\\_(?=[A-Za-z])", "-", data)
        data = re.sub(r"\\dots", "...", data)
        data = re.sub(r"\$\\rightarrow\$", "→", data)
        data = re.sub(r"\$\\nrightarrow\$", "↛", data)
        data = re.sub(r"\$_{\\text{\\backposs}}\$", "<sub>[[`$]]</sub>", data)
        data = re.sub(r"\$_{\\text{", '<sub>', data)
        data = re.sub(r"}}\$", '</sub>', data)
        data = re.sub(r"\$_{", '<sub>', data)
        data = re.sub(r"}\$", '</sub>', data)
        data = re.sub(r"\backi", '</sub>', data)

        # misc labels
        data = replace_circumfixes(data, r'\\sst{', '<i>', '</i>')
        data = replace_circumfixes(data, r'\\lbl{', '<i>', '</i>')
        data = replace_circumfixes(data, r'\\pex{', '<i>', '</i>')

        data = replace_circumfixes(data, r'\\choices{', r'<choices>', r'</choices>')
        # underlining
        while '<choices>' in data:
            start = data.index('<choices>')
            end = data.index('</choices>')
            data = data[:start] + data[start:end].replace(r'\\', '</u>/<u>') + data[end:]
            data = data.replace('<choices>', '<u>', 1)
            data = data.replace('</choices>', '</u>', 1)

        data = replace_circumfixes(data, r'\\url{', '', '')

        data = re.sub(r'\\psstX{Part/Portion}{Part/Portion}', " [[Part/Portion]] ", data)

        data = re.sub(r"\\end{history}", "}", data)
        data = replace_circumfixes(data, r'\\begin{history}', '\n<!-- ', ' -->')
        data = replace_circumfixes(data, r'\\futureversion{', '\n<!-- ', ' -->')

        # handle footnotes, citations, references
        data = replace_circumfixes(data, r'\\footnote{', '<footnote1>fn:', '</footnote1>')
        data = re.sub(r'\\Citep', '\citep', data)
        data = re.sub(r'\\Citet', '\citet', data)
        data = re.sub(r'\\citep\[', '\citep{', data)
        data = re.sub(r'\\citet\[', '\citet{', data)
        data = re.sub(r'\]{', ', ', data)
        data = replace_circumfixes(data, r'\\citep{', '<cite>', '</cite>')
        data = replace_circumfixes(data, r'\\citet{', '<cite>', '</cite>')
        data = replace_circumfixes(data, r'\\cref{', '<ref>', '</ref>')
        data = replace_circumfixes(data, r'\\ref{', '<ref>', '</ref>')
        data = replace_circumfixes(data, r'\\exp{', '<exp>', '</exp>')
        data = replace_circumfixes(data, r'\\Cref{', '<ref>', '</ref>')
        j = 1
        for i in [1, 2]:
            m = re.compile('<footnote'+str(i)+'>(.*?)</footnote'+str(i)+'>', re.MULTILINE|re.DOTALL)
            while m.search(data):
                s = m.search(data).group(1)
                s = re.sub('<(/)?footnote[12]>', '', s)
                footnotes.append(s)
                data = m.sub('[^' + str(j) + ']', data, count=1)
                j += 1
        # add footnotes
        k = 1
        for foot in footnotes:
            data += '\n[^'+str(k)+']: '+foot.replace('fn:','')
            k += 1

        # handle examples
        data = handle_ex(data)

        data = re.sub(r"\\(end|begin){(.*?)}", "", data)

        # whitespace
        data = re.sub(r"\n\s+\n", "\n\n", data)
        data = re.sub(r"\n\n+\n", "\n\n", data)

        # fix various junk
        data = re.sub(r'{[0-9]*}', '', data)
        data = data.replace(r'\_', '_')
        data = data.replace('{}', '')
        data = data.replace('][', '] [')
        data = re.sub('][(](?=[^/])', '] (', data)
        # data = data.replace(r'\ex', '')
        data = data.replace('Part-Portion','PartPortion')
        data = data.replace('Part/Portion', 'PartPortion')
        data = re.sub(r'</ex>\s*','</ex>\n\n',data)
        data = re.sub(r'</sn>\s*', '</sn>\n\n', data)
        while re.search('<ex><label>(?P<label>.*?)</label></ex>\s+<ex>',data):
            x = re.search('<ex><label>(?P<label>.*?)</label></ex>\s+<ex>',data)
            label = x.group('label')
            data = data.replace(x.group(0),'<ex><label>'+label+'</label>')

    with open(ofile, 'w+', encoding='utf8') as f:

        f.write(data)



for file in os.listdir(dir1):
    print(file)
    if not os.path.exists(dir2):
        os.makedirs(dir2)
    if file.endswith('.tex'):
        convert(os.path.join(dir1,file),
                os.path.join(dir2,file.replace('.tex','.txt')),
                file.replace('.tex',''))
