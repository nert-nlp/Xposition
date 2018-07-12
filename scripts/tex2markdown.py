#coding=utf-8

"""
This code is for importing our Preposition Supersense v2 guidelines
into our new Xposition website/wiki
3/21/18 Austin Blodgett
"""
import re, os

dir1 = 'tex'
dir2 = 'markdown'

class ConvertLatexByLine:

    list_num = 1

    def delete_junk(self, line):
        # latex comments
        if line.strip().startswith('%'):
            line = ''
        elif re.search(r'(?<=[^\\])%', line):
            line = line[:re.search(r'(?<=[^\\])%', line).start()]
        # junk
        if 'multicol' in line or '\\bibliography' in line or '\\printindex' in line:
            line = ''
        elif r'\noindent' in line:
            line = line.replace(r'\noindent', '')
        return line


    def convert_punctuation(self, line):
        # take care of [] brackets
        line = re.sub(r'\[\[', r'\[', line)
        line = re.sub(r'\]\]', r'\]', line)
        # punctuation
        line = re.sub('``', "“", line)
        line = re.sub('`', "‘", line)
        line = re.sub("''", "”", line)
        line = re.sub("'", "’", line)
        line = re.sub("---", "—", line)
        line = re.sub(r"[.]\\ ", ". ", line)  # e.g. "etc.\ " in LaTeX within a sentence to ensure it is followed by a normal-size space
        line = re.sub(r"~~", " ", line)
        line = re.sub(r"~", " ", line)

        # underscore
        line = line.replace(r'\_', '_')

        return line

    def convert_lists(self, line):
        # add numbered list
        if r'\begin{itemize}' in line or r'\begin{enumerate}' in line:
            self.list_num = 1
        if r'\item' in line:
            line = line.replace(r'\item', str(self.list_num) + '.')
            self.list_num += 1
        return line

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
    def convert_citations(self, line):
        line = re.sub(r'\\Citep', '\cite', line)
        line = re.sub(r'\\Citet', '\cite', line)
        line = re.sub(r'\\citep', '\cite', line)
        line = re.sub(r'\\citet', '\cite', line)

        CITE_REs = [re.compile(r'\\cite\[(?P<op1>.*?)\]\[(?P<op2>.*?)\]{(?P<label>.+?)}'),
                    re.compile(r'\\cite\[(?P<op2>.*?)\]{(?P<label>.+?)}'),
                    re.compile(r'\\cite{(?P<label>.+?)}')]
        for index, p in enumerate(CITE_REs):
            while p.search(line):
                cite = p.search(line).group('label')
                op1 = ''
                op2 = ''
                if index == 0:
                    op1 = p.search(line).group('op1')
                    op1 = op1 + ' ' if op1.strip() else ''
                if index in [0,1]:
                    op2 = p.search(line).group('op2')
                    op2 = ', ' + op2.strip() if op2 else ''
                cites = [c.strip() for c in cite.split(',')]
                for i, c in enumerate(cites):
                    if c in self.CITATIONS:
                        cites[i] = '[' + self.CITATIONS[c] + ']'\
                                       +'(/bib/' + self.CITATIONS[c].replace(' ', '_').replace(',', '').replace('.', '') + '/)'
                line = line.replace(p.search(line).group(), '(' + op1 + ', '.join(cites) + op2 + ')')
        return line

class ConvertLatexMultiline:

    def merge_lines(self, line1, line2):
        i = line1.index(line1.strip()) + len(line1.strip())
        j = line2.index(line2.strip())
        # print('1',line1[:i])
        # print('2',line2[j:])
        return line1[:i] + ' ' + line2[j:]

    def circum_replace(self, text='', prefix='{', suffix='}', rprefix='', rsuffix='', max=None):
        while re.search(prefix, text) and (not max or max > 0):
            m = re.search(prefix, text)
            start = m.end()
            contents = ''
            i = 0
            count = 1 # assume '{' in prefix
            while not (suffix in contents and count == 0):
                ch = text[start + i]
                if ch == '{': count += 1
                elif ch == '}': count -= 1
                i += 1
                if count == 0: break
                contents += ch

            text = text[:m.start()] + rprefix + contents + rsuffix + text[start + i:]
            if max: max -= 1
        return text

    def convert_math(self, text):
        # math
        text = text.replace("\\slash ", "/")
        text = text.replace("\\dots", "...")
        text = text.replace("$\\rightarrow$", "→")
        text = text.replace("$\\nrightarrow$", "↛")
        text = text.replace("$_{\\text{\\backposs}}$", "<sub>[[`$]]</sub>")
        text = self.circum_replace(text=text, prefix=r"\$_{\\text{", suffix=r"}}\$", rprefix='<sub>', rsuffix='</sub>')
        text = self.circum_replace(text=text, prefix=r"\$_{", suffix=r"}\$", rprefix='<sub>', rsuffix='</sub>')
        return text

    def convert_basic(self, text):
        # handle shortdef
        text = self.circum_replace(text=text, prefix=r'\\shortdef{', rprefix='|', rsuffix='|')
        # subsection
        text = self.circum_replace(text=text, prefix=r'\\subsection{', rprefix='##')
        text = self.circum_replace(text=text, prefix=r'\\subsubsection{', rprefix='###')
        # handle paragraph
        text = self.circum_replace(text=text, prefix=r'\\paragraph{', rprefix='**', rsuffix='**\n\n')
        # handle bold, italics, quotes
        text = self.circum_replace(text=text, prefix=r'\\textbf{', rprefix='**', rsuffix='**')
        text = self.circum_replace(text=text, prefix=r'\\textit{', rprefix='<i>', rsuffix='</i>')
        text = self.circum_replace(text=text, prefix=r'\\w{', rprefix='<i>', rsuffix='</i>')
        text = self.circum_replace(text=text, prefix=r'\\emph{', rprefix='<i>', rsuffix='</i>')
        text = self.circum_replace(text=text, prefix=r'\\uline{', rprefix='<u>', rsuffix='</u>')
        text = self.circum_replace(text=text, prefix=r'\\texttt{', rprefix='`', rsuffix='`')
        return text


    def convert_custom(self, text):
        # handle \p{}
        text = self.circum_replace(text=text, prefix=r'#\\p{', rprefix='#')
        text = self.circum_replace(text=text, prefix=r'\*\\p{', rprefix='*')
        text = self.circum_replace(text=text, prefix=r'\\p{', rprefix=' [[en/', rsuffix=']] ')
        # handle \p*{}{}
        text = self.circum_replace(text=text, prefix=r'\\p\*{', rprefix='\\p1{', rsuffix='](/en/\\p2')
        text = self.circum_replace(text=text, prefix=r'\\p2{', rprefix='', rsuffix='}')
        text = self.circum_replace(text=text, prefix=r'\\p1{', rprefix=' [', rsuffix=') ')
        # handle \psst{}
        text = self.circum_replace(text=text, prefix=r'\\psst{', rprefix=' [[', rsuffix=']] ')
        # handle \rf{}{}
        text = self.circum_replace(text=text, prefix=r'\\rf{', rprefix='\\rf1{', rsuffix='--\\rf2')
        text = self.circum_replace(text=text, prefix=r'\\rf2{', rprefix='', rsuffix='}')
        text = self.circum_replace(text=text, prefix=r'\\rf1{', rprefix=' [[', rsuffix=']] ')
        # reformat links
        while re.search(r' \[\[(.*?)\]\] ', text):
            ref = re.search(r' \[\[(.*?)\]\] ', text).group(1)
            text = text.replace(' [[' + ref + ']] ', '[' + ref + '](/' + ref + ')')
        text = re.sub(r'\[en/', '[', text)
        
        # labels
        text = self.circum_replace(text=text, prefix=r'\\label{', rprefix='<label>', rsuffix='</label>')
        # references
        text = self.circum_replace(text=text, prefix=r'\\cref{', rprefix='<ref>', rsuffix='</ref>')
        text = self.circum_replace(text=text, prefix=r'\\cref{', rprefix='<ref>', rsuffix='</ref>')
        text = self.circum_replace(text=text, prefix=r'\\ref{', rprefix='<ref>', rsuffix='</ref>')
        text = self.circum_replace(text=text, prefix=r'\\Cref{', rprefix='<ref>', rsuffix='</ref>')
        
        # choices
        text = self.circum_replace(text=text, prefix=r'\\choices{', rprefix=r'<choices>', rsuffix=r'</choices>')
        # underlining
        while '<choices>' in text:
            start = text.index('<choices>')
            end = text.index('</choices>')
            text = text[:start] + text[start:end].replace(r'\\', '</u>/<u>') + text[end:]
            text = text.replace('<choices>', '<u>', 1)
            text = text.replace('</choices>', '</u>', 1)

        # special characters
        text = text.replace(r'\backi', '[[`i]]')
        text = text.replace(r'\backc', '[[`c]]')
        text = text.replace(r'\backd', '[[`d]]')
        text = text.replace(r'\backposs', '[[`$]]')

        # misc
        text = self.circum_replace(text=text, prefix=r'\\sst{', rprefix='<i>', rsuffix='</i>')
        text = self.circum_replace(text=text, prefix=r'\\lbl{', rprefix='<i>', rsuffix='</i>')
        text = self.circum_replace(text=text, prefix=r'\\pex{', rprefix='<i>', rsuffix='</i>')

        # custom fixes
        # toward(s), out(_of), and off(_of)
        text = text.replace('[toward(s)](/en/toward(s))', '[toward](/en/toward)/[towards](/en/towards)')
        text = text.replace('[off(_of)](/en/off(_of))', '[off](/en/off)/[off_of](/en/off_of)')
        text = text.replace('[out(_of)](/en/out(_of))', '[out](/en/out)/[out_of](/en/out_of)')
        text = text.replace('[as](/en/as)--[as](/en/as)', '[as](/en/as)—[as](/en/as)')

        # PartPortion
        text = re.sub(r'\\psstX{Part/Portion}{Part/Portion}', " [[PartPortion]] ", text)
        text = text.replace('Part-Portion', 'PartPortion')
        text = text.replace('Part/Portion', 'PartPortion')

        # latex junk
        text = self.circum_replace(text=text, prefix=r'\\textsubscript{', rprefix='<sub>', rsuffix='</sub>')
        text = self.circum_replace(text=text, prefix=r'\\mbox{')
        text = self.circum_replace(text=text, prefix=r'\\url{')
        text = re.sub(r"\\end{history}", "}", text)
        text = self.circum_replace(text=text, prefix=r'\\begin{history}', rprefix='\n<!-- ', rsuffix=' -->')
        text = self.circum_replace(text=text, prefix=r'\\futureversion{', rprefix='\n<!-- ', rsuffix=' -->')

        return text

    def convert_footnotes(self, text):
        footnotes = []
        # handle footnotes, references
        text = self.circum_replace(text=text, prefix=r'\\footnote{', rprefix='<footnote1>fn:', rsuffix='</footnote1>')
        j = 1
        for i in [1, 2]:
            m = re.compile('<footnote' + str(i) + '>(.*?)</footnote' + str(i) + '>', re.MULTILINE | re.DOTALL)
            while m.search(text):
                s = m.search(text).group(1)
                s = re.sub('<(/)?footnote[12]>', '', s)
                footnotes.append(s)
                text = m.sub('[^' + str(j) + ']', text, count=1)
                j += 1
        # add footnotes
        k = 1
        for foot in footnotes:
            text += '\n[^' + str(k) + ']: ' + foot.replace('fn:', '').replace('\n', ' ').replace('\t', '')
            k += 1
        return text

    def convert_examples(self, text):
        text = re.sub(r'\\ex(?=\\)', r'\ex ', text)
        text = re.sub(r'\\ex\t', '\ex ', text)
        text = re.sub(r'\\sn(?=\\)', r'\sn ', text)
        text = re.sub(r'\\sn\t', '\sn ', text)
        text = re.sub(r'\\exp{.*?}', r'\ex ', text)
        text = re.sub(r'\s*(?=\\begin{)', '\n', text)

        for ex in ['ex','sn']:
            match = re.compile(r'\\'+ex+'(?=\W)')
            while match.search(text):
                m = match.search(text)
                if text[m.end()] == '{':
                    text = self.circum_replace(text=text, prefix='\\'+ex+'{', rprefix='<'+ex+'>', rsuffix='</'+ex+'>', max=1)
                else:
                    start = m.end()
                    x = re.compile(r'(\t*\\(ex|sn)|\\end|\\begin|\t*- <ex>)').search(text, pos=start)
                    x = x or re.compile(r'\n').search(text, pos=start)
                    end = x.start()

                    content = '\n- <'+ex+'>' + text[start:end].strip() + '</'+ex+'>\n\n'
                    text = text[:m.start()] + content + text[end:]

        # fix junk
        text = re.sub(r'</ex>\n*', '</ex>\n\n', text)
        text = re.sub(r'</sn>\n*', '</sn>\n\n', text)
        while re.search('<ex><label>(?P<label>.*?)</label></ex>\s+<ex>', text):
            x = re.search('<ex><label>(?P<label>.*?)</label></ex>\s+<ex>', text)
            label = x.group('label')
            text = text.replace(x.group(), '<ex><label>' + label + '</label>')
        # move </ex> before \begin{xlist}
        while re.search(r'\\begin{.*?}</ex>', text):
            x = re.search(r'\\begin{.*?}</ex>', text)
            text = text.replace(x.group(), '</ex>\n'+x.group().replace('</ex>', ''))
        # get rid of \n in example
        for x in re.finditer(r'<ex>.*?</ex>', text, re.DOTALL):
            if '\n' in x.group():
                text = text.replace(x.group(), x.group().strip().replace('\n',' '))
        return text

    def convert_indentation(self, text):
        text = text.replace('\r','')
        text = text.replace('\t', ' ')
        text = re.sub(r"\n\s+\n", "\n\n", text)

        # indentation
        new_lines = []
        depth = 0
        lines = [l+'\n' for l in text.split('\n')]
        for line in lines:
            # keep track of sublist tabs
            if re.search(r'\\begin{(xlist|exe|enumerate|itemize)}', line):
                depth += len(re.findall(r'\\begin{(xlist|exe|enumerate|itemize)}', line))
            if re.search(r'\\end{(xlist|exe|enumerate|itemize)}', line):
                depth -= len(re.findall(r'\\end{(xlist|exe|enumerate|itemize)}', line))
            start = ''.join(['\t' for x in range(depth - 1)])
            end = line[-1] if line and line[-1] in [' ', '\n'] else ''
            line = start + line.strip() + end
            new_lines.append(line)
        text = ''.join(new_lines)
        text = re.sub(r"\t*\\(end|begin){(.*?)}\n*", "", text)
        text = re.sub(r'\t*- <ex></ex>\n*', '', text)

        previous_depth = 0
        depth = 0
        new_lines = []
        lines = [l + '\n' for l in text.split('\n')]
        for line in lines:
            depth = len(re.match('^\t*', line).group()) if line.strip() else depth
            start = ''.join(['\t' for x in range(depth)])
            if depth - previous_depth > 1:
                start = ''.join(['\t' for x in range(previous_depth+1)])
            end = line[-1] if line and line[-1] in [' ', '\n'] else ''
            line = start + line.strip() + end
            new_lines.append(line)
            previous_depth = depth
        text = ''.join(new_lines)

        # merge lines
        lines = [l + '\n' for l in text.split('\n')]
        for line1, line2 in zip([''] + lines, lines + ['']):
            if not re.match('.*\w.*', line1) or not re.match('.*\w.*', line2):
                continue
            # ends or starts in lower case letter
            if re.match('[a-z].*$', line2) or re.match('.*[a-z]$', line1):
                text = text.replace(line1 + line2, self.merge_lines(line1, line2))
            # ends in comma
            if re.match('.*,$', line1):
                text = text.replace(line1 + line2, self.merge_lines(line1, line2))
            # keep lines
            if re.match(r'[0-9]+\. ', line1) and line1.strip()[-1] not in [':', '.', '?']:
                text = text.replace(line1 + line2, self.merge_lines(line1, line2))
        return text

    def convert_sublist_spacing(self, text):
        depth = 0
        previous_depth = 0
        # remove blank lines if they would mess up markup of sublists
        lines = [line + '\n' for line in text.split('\n') if line.strip()]
        for line1, line2 in zip([''] + lines, lines + ['']):
            # keep track of sublist tabs
            depth = len(re.match('^\t*', line2).group())
            if depth > previous_depth:
                text = re.sub(re.escape(line1) + '\s*' + re.escape(line2), line1 + line2, text)
            elif re.match('^([0-9]+\.|- ).*', line2.strip()):
                text = re.sub(re.escape(line1) + '\s*' + re.escape(line2), line1 +'\n'+ line2, text)
            previous_depth = depth

        # add '- ' on previous line if missing
        depth = 0
        previous_depth = 0
        lines = [line + '\n' for line in text.split('\n')]
        for line1, line2 in zip([''] + lines, lines + ['']):
            depth = len(re.match('^\t*', line2).group()) if line2.strip() else depth
            if depth > previous_depth and not re.match('^([0-9]+\.|- ).*', line1.strip()) and line1.strip():
                text = text.replace(line1+line2, '\n- '+line1+line2)
            previous_depth = depth
        return text

    def convert_last(self, text):
        # late stage junk
        text = re.sub(r'\n\s*(- )?{?[0-9]*}?\s*\n', '\n\n', text)
        text = re.sub('][(](?=[^/])', '] (', text)
        text = re.sub(r'\t*- <ex></ex>', '', text)
        text = text.replace('{}','')

        # whitespace
        text = re.sub(r"\n\s+\n", "\n\n", text)
        text = re.sub(r" {2}", " ", text)

        # backspaces
        text = text.replace("\\$", "$")
        text = text.replace("\\#", "#")
        text = text.replace("\\%", "%")
        text = text.replace(r'\{', '{')
        text = text.replace(r'\}', '}')
        text = text.replace("\\\\", " ")
        text = text.replace("\\ ", " ")
        text = text.replace("etc.\\", "etc.")
        text = text.replace("etc.)\\", "etc.)")

        return text

def convert_file(ifile, ofile, title):

    with open(ifile, 'r', encoding='utf8') as f:
       
        convert_line = ConvertLatexByLine()
        convert_multiline = ConvertLatexMultiline()


        lines = f.readlines()


        new_lines = []
        # single line conversions
        for line in lines:
            # embold title of article
            line = line.replace(r'\section{'+title+'}', '')
            # line = re.sub(r'\\psst{' + title + '}', '**' + title + '**', line)
            line = convert_line.delete_junk(line)
            line = convert_line.convert_lists(line)
            line = convert_line.convert_punctuation(line)
            line = convert_line.convert_citations(line)
            new_lines.append(line)

        text = ''.join(new_lines)

        # multiline conversions
        text = convert_multiline.convert_basic(text)
        text = convert_multiline.convert_math(text)
        text = convert_multiline.convert_custom(text)
        text = convert_multiline.convert_footnotes(text)
        text = convert_multiline.convert_examples(text)
        text = convert_multiline.convert_indentation(text)
        text = convert_multiline.convert_sublist_spacing(text)

        # last conversions
        text = convert_multiline.convert_last(text)

        # print(text)

    with open(ofile, 'w+', encoding='utf8') as f:
        f.write(text)



for file in os.listdir(dir1):
    print(file)
    if not os.path.exists(dir2):
        os.makedirs(dir2)
    if file.endswith('.tex'):
        convert_file(os.path.join(dir1,file),
                os.path.join(dir2,file.replace('.tex','.txt')),
                file.replace('.tex',''))
