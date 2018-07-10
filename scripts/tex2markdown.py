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

def circum_replace_1(s, prefix, repl_prefix, repl_suffix):
    m = re.search(prefix,s)
    start_index = m.end()
    contents = ''
    i=0
    count = 1
    while True:
       c = s[start_index+i]
       if c=='{': count += 1
       elif c=='}': count -= 1
       if count == 0: break
       contents += c
       i+=1
    s1 = s[:m.start()]
    s2 = repl_prefix + contents + repl_suffix
    s3 = s[start_index+i+1:]
    return s1 + s2 + s3

def circum_replace(s, prefix, repl_prefix, repl_suffix):
    while re.search(prefix,s):
        s = circum_replace_1(s, prefix, repl_prefix, repl_suffix)
    return s

def handle_ex(s):
    # global example_index
    s = re.sub(r",(\s)(\s)+", ", ", s, re.MULTILINE)
    s = re.sub(r"(?<=[a-z])(\s+)(?=[a-z])", " ", s, re.MULTILINE)
    # s = re.sub(r"(?<=\S)([ \t]*)\\ex", "\n\ex", s)
    s = re.sub(r'\\ex(?=\\)', r'\ex ', s)
    s = re.sub(r'\\ex\t', '\ex ', s)
    s = re.sub(r'\\sn(?=\\)', r'\sn ', s)
    s = re.sub(r'\\sn\t', '\sn ', s)
    s = re.sub(r'\\exp{.*?}', r'\ex ', s)


    match = re.compile(r'\\ex(?=\W)')
    while match.search(s):
        m = match.search(s)
        if s[m.end()]=='{':
            s = circum_replace_1(s, r'\\ex{', '<ex>', '</ex>')
        else:
            start = m.end()
            x = re.compile(r'(\t*\\(ex|sn)|\\end)').search(s, pos=start)
            x = x or re.compile(r'\n').search(s, pos=start)
            end = x.start()

            content = '<ex>' + s[start:end].strip().replace('\n',' ') + '</ex>'
            s = s[:m.start()]+content+'\n'+s[end:]

    match = re.compile(r'\\sn(?=\W)')
    while match.search(s):
        m = match.search(s)
        if s[m.end()] == '{':
            s = circum_replace_1(s, r'\\sn{', '<sn>', '</sn>')
        else:
            start = m.end()
            x = re.compile(r'(\t*\\(ex|sn)|\\end|<ex>)').search(s, pos=start)
            x = x or re.compile(r'\n').search(s, pos=start)
            end = x.start()
            content = '<sn>' + s[start:end].strip().replace('\n', ' ') + '</sn>'
            s = s[:m.start()] + content + '\n' + s[end:]

    return s


def convert(ifile, ofile, title):
    list_num = 1
    depth = 0
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
            # latex comments
            if re.search(r'(?<=[^\\])%', f[i]):
                f[i] = f[i][:re.search(r'(?<=[^\\])%', f[i]).start()]
            # take care of [] brackets
            f[i] = re.sub(r'\[\[', r'\[', f[i])
            f[i] = re.sub(r'\]\]', r'\]', f[i])
            # add numbered list
            if r'\begin{itemize}' in f[i] or r'\begin{enumerate}' in f[i]:
                list_num = 1
            if r'\item' in f[i]:
                f[i] = f[i].replace(r'\item', str(list_num) + '.')
                # try to get it on one line
                if f[i].strip()[-1] not in ['.',':','?']:
                    end = f[i+1][-1] if f[i+1] and f[i+1][-1] in [' ', '\n'] else ''
                    f[i] = f[i].replace('\n',' ') + f[i+1].strip() + end
                    f[i+1] = ''
                list_num += 1
            # junk
            if '\\bibliography' in f[i]:
                f[i] = ''
            if '\\printindex' in f[i]:
                f[i] = ''
            # junk whitespace
            f[i] = re.sub(r'\r', r'', f[i])
            start = ''.join(['\t' for x in range(depth-1)])
            end = f[i][-1] if f[i] and f[i][-1] in [' ','\n'] else ''
            f[i] = start + f[i].strip() + end
            # keep track of sublist tabs
            if re.search(r'\\begin{(xlist|exe|enumerate|itemize)}', f[i]):
                depth +=1
            if re.search(r'\\end{(xlist|exe|enumerate|itemize)}', f[i]):
                depth -=1


        data = ''.join(f[1:])

        # handle shortdef
        data = circum_replace(data, r'\\shortdef{', r'|', '|')

        # subsection
        data = circum_replace(data, r'\\subsection{', '##', '')
        data = circum_replace(data, r'\\subsubsection{', '###', '')

        # embold title of article
        data = re.sub(r'\\psst{' + title + '}', '**' + title + '**', data)

        # handle \p{}
        data = circum_replace(data, r'#\\p{', '#', '')
        data = circum_replace(data, r'\*\\p{', '*', '')
        data = circum_replace(data, r'\\p{', ' [[en/', ']] ')
        # handle \p*{}{}
        data = circum_replace(data, r'\\p\*{', '\\p1{', '](/en/\\p2')
        data = circum_replace(data, r'\\p2{', '', '}')
        data = circum_replace(data, r'\\p1{', ' [', ') ')
        # handle \psst{}
        data = circum_replace(data, r'\\psst{', ' [[', ']] ')
        # handle \rf{}{}
        data = circum_replace(data, r'\\rf{', '\\rf1{', '--\\rf2')
        data = circum_replace(data, r'\\rf2{', '', '}')
        data = circum_replace(data, r'\\rf1{', ' [[', ']] ')
        # reformat links
        while re.search(r' \[\[(.*?)\]\] ', data):
            ref = re.search(r' \[\[(.*?)\]\] ', data).group(1)
            data = data.replace(' [[' + ref + ']] ', '[' + ref + '](/' + ref + ')')
        data = re.sub(r'\[en/', '[', data)
        data = circum_replace(data, r'\\label{', '<label>', '</label>')

        # handle paragraph
        data = circum_replace(data, r'\\paragraph{', '- **', '**')

        # handle bold, italics, quotes
        data = circum_replace(data, r'\\textbf{', '**', '**')
        data = circum_replace(data, r'\\textit{', '<i>', '</i>')
        data = circum_replace(data, r'\\w{', '<i>', '</i>')
        data = circum_replace(data, r'\\emph{', '<i>', '</i>')
        data = circum_replace(data, r'\\uline{', '<u>', '</u>')
        data = circum_replace(data, r'\\texttt{', '`', '`')

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
        data = circum_replace(data, r'\\textsubscript{', '<sub>', '</sub>')
        data = circum_replace(data, r'\\mbox{', '', '')

        # misc labels
        data = circum_replace(data, r'\\sst{', '<i>', '</i>')
        data = circum_replace(data, r'\\lbl{', '<i>', '</i>')
        data = circum_replace(data, r'\\pex{', '<i>', '</i>')

        # special characters
        data = data.replace(r'\backi', '[[`i]]')
        data = data.replace(r'\backc', '[[`c]]')
        data = data.replace(r'\backd', '[[`d]]')
        data = data.replace(r'\backposs', '[[`$]]')

        data = circum_replace(data, r'\\choices{', r'<choices>', r'</choices>')
        # underlining
        while '<choices>' in data:
            start = data.index('<choices>')
            end = data.index('</choices>')
            data = data[:start] + data[start:end].replace(r'\\', '</u>/<u>') + data[end:]
            data = data.replace('<choices>', '<u>', 1)
            data = data.replace('</choices>', '</u>', 1)

        data = circum_replace(data, r'\\url{', '', '')

        data = re.sub(r'\\psstX{Part/Portion}{Part/Portion}', " [[PartPortion]] ", data)

        data = re.sub(r"\\end{history}", "}", data)
        data = circum_replace(data, r'\\begin{history}', '\n<!-- ', ' -->')
        data = circum_replace(data, r'\\futureversion{', '\n<!-- ', ' -->')

        # add citations
        CITATIONS = {
            'bonial-18': 'Bonial et al., 2018',
            'verbnet': 'Kipper et al., 2008',
            'palmer-17': 'Palmer et al., 2017',
            'chang-98': 'Chang et al., 1998',  # p. 230,
            'cgel': 'Huddleston and Pullum, 2002',  # p. 1224,
            'schmid-00': 'Schmid, 2000',
            'yadurajan-01': 'Yadurajan, 2001',  # p. 7,
            'pustejovsky-91': 'Pustejovsky, 1991',
            'klein-94': 'Klein, 1994',  # pp. 154--157,
            'talmy-96': 'Talmy, 1996',
            'baldwin-06': 'Baldwin et al., 2006',
            'amr': 'Banarescu et al., 2013',  # AMR;][,
            'amr-guidelines': 'Banarescu et al., 2015',
            'srikumar-13': 'Srikumar and Roth, 2013a',
            'srikumar-13-inventory': 'Srikumar and Roth, 2013b'
        }

        data = re.sub(r'\\Citep', '\cite', data)
        data = re.sub(r'\\Citet', '\cite', data)
        data = re.sub(r'\\citep', '\cite', data)
        data = re.sub(r'\\citet', '\cite', data)

        CITE_RE1 = re.compile(r'\\cite\[(?P<op1>.*?)\]\[(?P<op2>.*?)\]{(?P<label>.+?)}')
        CITE_RE2 = re.compile(r'\\cite\[(?P<op2>.*?)\]{(?P<label>.+?)}')
        CITE_RE3 = re.compile(r'\\cite{(?P<label>.+?)}')
        while CITE_RE1.search(data):
            cite = CITE_RE1.search(data).group('label')
            op1 = CITE_RE1.search(data).group('op1')
            op2 = CITE_RE1.search(data).group('op2')
            op1 = op1+' ' if op1 else ''
            op2 = ', '+op2 if op2 else ''
            cites = [c.strip() for c in cite.split(',')]
            for i, c in enumerate(cites):
                if c in CITATIONS:
                    cites[i] = '[' + CITATIONS[c] + '](/bib/' + CITATIONS[c].replace(' ', '_').replace(',', '').replace(
                        '.', '') + '/)'
            data = data.replace(CITE_RE1.search(data).group(0), '(' + op1 + ', '.join(cites) + op2 +')')
        while CITE_RE2.search(data):
            cite = CITE_RE2.search(data).group('label')
            op2 = CITE_RE2.search(data).group('op2')
            op2 = ', '+op2 if op2 else ''
            cites = [c.strip() for c in cite.split(',')]
            for i, c in enumerate(cites):
                if c in CITATIONS:
                    cites[i] = '[' + CITATIONS[c] + '](/bib/' + CITATIONS[c].replace(' ', '_').replace(',', '').replace(
                        '.', '') + '/)'
            data = data.replace(CITE_RE2.search(data).group(0), '(' +', '.join(cites) + op2 +')')
        while CITE_RE3.search(data):
            cite = CITE_RE3.search(data).group('label')
            cites = [c.strip() for c in cite.split(',')]
            for i, c in enumerate(cites):
                if c in CITATIONS:
                    cites[i] = '[' + CITATIONS[c] + '](/bib/' + CITATIONS[c].replace(' ', '_').replace(',', '').replace(
                        '.', '') + '/)'
            data = data.replace(CITE_RE3.search(data).group(0), '(' +', '.join(cites) + ')')


        # handle footnotes, references
        data = circum_replace(data, r'\\footnote{', '<footnote1>fn:', '</footnote1>')
        data = circum_replace(data, r'\\cref{', '<ref>', '</ref>')
        data = circum_replace(data, r'\\cref{', '<ref>', '</ref>')
        data = circum_replace(data, r'\\ref{', '<ref>', '</ref>')
        # data = circum_replace(data, r'\\exp{', '<exp>', '</exp>')
        data = circum_replace(data, r'\\Cref{', '<ref>', '</ref>')
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

        # fix various junk
        data = re.sub(r"\\(end|begin){(.*?)}", "", data)
        data = re.sub(r'{[0-9]*}', '', data)
        data = data.replace(r'\_', '_')
        data = data.replace('{}', '')
        # data = data.replace('][', '] [')
        data = re.sub('][(](?=[^/])', '] (', data)
        # data = data.replace(r'\ex', '')
        data = data.replace('Part-Portion','PartPortion')
        data = data.replace('Part/Portion', 'PartPortion')
        data = re.sub(r'</ex>\n*','</ex>\n\n',data)
        data = re.sub(r'</sn>\n*', '</sn>\n\n', data)
        while re.search('<ex><label>(?P<label>.*?)</label></ex>\s+<ex>',data):
            x = re.search('<ex><label>(?P<label>.*?)</label></ex>\s+<ex>',data)
            label = x.group('label')
            data = data.replace(x.group(0),'<ex><label>'+label+'</label>')
        data = data.replace(r'<ex></ex>', '')

        # backspaces
        data = data.replace("\\$", "$")
        data = data.replace("\\#", "#")
        data = data.replace("\\%", "%")
        # data = data.replace(r"\\{}", " ")
        data = data.replace(r'\{', '{')
        data = data.replace(r'\}', '}')
        data = data.replace("\\\\", " ")
        data = data.replace("\\ ", " ")
        data = data.replace("etc.\\", "etc.")
        data = data.replace("etc.)\\", "etc.)")

        # whitespace
        data = re.sub(r"\n\s+\n", "\n\n", data)
        data = re.sub(r"\n\n+\n", "\n\n", data)
        data = re.sub(r" {2}", " ", data)

        # toward(s), out(_of), and off(_of)
        data = data.replace('[toward(s)](/en/toward(s))', '[toward](/en/toward)/[towards](/en/towards)')
        data = data.replace('[off(_of)](/en/off(_of))', '[off](/en/off)/[off_of](/en/off_of)')
        data = data.replace('[out(_of)](/en/out(_of))', '[out](/en/out)/[out_of](/en/out_of)')

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
