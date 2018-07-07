# coding=utf-8
import re, os

dir = 'markdown'
dir2 = 'markdown-and-macros'


P_RE = re.compile(r'\[([\w\\\'’-])+\]\(/en/(?P<p>[\w\'’\\-]+)\)')
SS_RE = re.compile(r'\[[\w$`-]+\]\(/(?P<ss>[\w$`-]+)\)')
HEADER_RE = re.compile('^(\w)?.*'+SS_RE.pattern+'.*:$') # [PartPortion](/PartPortion) is used ...:
ALT_SS_RE = re.compile('\('+SS_RE.pattern+'\)')
ORDINARY_RE = re.compile('^(\[|\w).*$')
EXAMPLE_RE = re.compile('<(ex|sn)>(?P<ex>.+?)</(ex|sn)>')
LABEL_RE = re.compile('<label>(?P<label>.+?)</label>')
REF_RE = re.compile('<(ref)>(?P<label>.+?)</(ref)>')
CITE_RE = re.compile('<cite>(?P<label>.+?)</cite>')
# EXP_RE = re.compile('<exp>(?P<label>.+?)</exp>')
# SN_RE = re.compile('<sn>(?P<ex>.+?)</sn>')


# EX_REF_RE = re.compile('\[[\w .,-]+?\]\(/(?P<ss>[\w$`-]+)/#ex(?P<id>\w+)\)')


class Examples:
    ids = {}
    labels = {}
    INDEX = 1

    def id(self, label):
        return self.ids[label]

    def label(self, title, id):
        return self.labels[(title, id)]

    def add_label_id(self, label, title, id=None):
        if not id: id = self.INDEX
        self.ids[label] = (title, id)
        self.labels[(title, id)] = label

    def convert_example(self, line):
        for example in EXAMPLE_RE.finditer(line):
            ex = example.group('ex').replace("'", r"\'").replace("\\", "\\\\").strip()
            if not re.search('\w',ex):
                line = line.replace(example.group(0),'')
                continue
            if not re.search(r'\[p \w\w/[\w\'’\\-]+ [\w$`-]+\]',ex):
                line = line.replace(example.group(0), ex)
                continue
            line = line.replace(example.group(0), '- [ex ' + str(self.INDEX).zfill(3) + ' ' + '\'' + ex + '\'' + ']')
            self.INDEX += 1
        return line

    def convert_ex_ref(self, line, title):
        for ex_link in REF_RE.finditer(line):
            label = ex_link.group('label')
            ls = label.split(',')
            ls = [l.strip() for l in ls]
            repl = []
            for l in ls:
                if l.startswith('ex:'):
                    if l in self.ids:
                        ss = self.id(l)[0]
                        id = self.id(l)[1]
                        repl.append('[exref ' + str(id).zfill(3) + ' ' + ss + ']')
                    else:
                        repl.append(l)
                        print('fix label', title, l)
                elif l.startswith('sec:') and l.replace('sec:','') in ['Species','Temporal','Path']:
                    repl.append('[ss ' + l.replace('sec:','') + ']')
                elif l.startswith('sec:') and l in self.ids:
                    ss = self.id(l)[0]
                    repl.append('[[ ' + ss + ']]')
                else:
                    repl.append(l)
                    print('fix label', title, l)

            line = line.replace(ex_link.group(0),'('+', '.join(repl)+')')
        return line


if not os.path.exists(dir2):
    os.makedirs(dir2)

examples = Examples()

for file in os.listdir(dir):
    if file.endswith('.txt'):
        with open(os.path.join(dir,file), 'r', encoding='utf8') as f:
            new_text = []


            title = file.replace('.txt', '').replace(' ','_')
            default_ss = title
            tmp_ss = None

            examples.INDEX = 1

            for line in f:
                # fix Part/Portion
                line = line.replace('Part/Portion', 'PartPortion')

                if HEADER_RE.match(line):
                    default_ss = SS_RE.search(line).group('ss')
                    # print(default_ss,line)
                elif ORDINARY_RE.match(line):
                    default_ss = title
                    # print(default_ss, line)
                elif ALT_SS_RE.search(line):
                    tmp_ss = ALT_SS_RE.search(line).group('ss')
                    # print(tmp_ss, line)
                elif '**'+file.replace('.txt', '')+'**' in line:
                    tmp_ss = file.replace('.txt', '')
                    # print(tmp_ss, line)
                # convert p
                for p_link in P_RE.finditer(line):
                    prep = p_link.group('p')
                    prep = re.sub('[’`]',"'",prep)
                    if EXAMPLE_RE.search(line):
                        line = line.replace(p_link.group(0),'[p en/' + prep + ' ' + (tmp_ss if tmp_ss else default_ss) + ']')
                    else:
                        line = line.replace(p_link.group(0), '[p en/' + prep + ']')
                # convert ss
                for ss_link in SS_RE.finditer(line):
                    ss = ss_link.group('ss')
                    line = line.replace(ss_link.group(0), '[ss '+ss+']')
                # add labels
                if LABEL_RE.search(line):
                    examples.add_label_id(LABEL_RE.search(line).group('label'), title)
                    line = LABEL_RE.sub('', line)
                # convert examples
                line = examples.convert_example(line)
                line = line.replace(r'    - [ex', '- [ex')
                if re.match('[}{]',line.strip()):
                    line = '\n'
                line = re.sub(r'<exp>.*?</exp>','',line)
                if '###' in line and line.strip()[-1] not in ['.',':','?']:
                    line = line.strip()+' '


                tmp_ss = None
                new_text.append(line)

            with open(os.path.join(dir2, file), 'w+', encoding='utf8') as f2:
                f2.write(''.join(new_text))

CITATIONS = {
    'bonial-18':'Bonial et al., 2018',
    'verbnet':'Kipper et al., 2008',
    'palmer-17':'Palmer et al., 2017',
    'chang-98':'Chang et al., 1998',#p. 230,
    'cgel':'Huddleston and Pullum, 2002',#p. 1224,
    'schmid-00':'Schmid, 2000',
    'yadurajan-01':'Yadurajan, 2001',#p. 7,
    'pustejovsky-91':'Pustejovsky, 1991',
    'klein-94':'Klein, 1994', #pp. 154--157,
    'talmy-96':'Talmy, 1996',
    'baldwin-06':'Baldwin et al., 2006',
    'amr':'Banarescu et al., 2013', #AMR;][,
    'amr-guidelines':'Banarescu et al., 2015',
    'srikumar-13':'Srikumar and Roth, 2013a',
    'srikumar-13-inventory':'Srikumar and Roth, 2013b'
}

for file in os.listdir(dir2):
    if file.endswith('.txt'):
        with open(os.path.join(dir2, file), 'r', encoding='utf8') as f:
            new_text = []
            for i, line in enumerate(f):
                # convert example refs
                line = examples.convert_ex_ref(line, file.replace('.txt',''))
                # add citations
                if CITE_RE.search(line):
                    cite = CITE_RE.search(line).group('label')
                    cites = [c.strip() for c in cite.split(',')]
                    for i,c in enumerate(cites):
                        if c in CITATIONS:
                            cites[i] = '['+CITATIONS[c]+'](/bib/'+CITATIONS[c].replace(' ','_').replace(',','').replace('.','')+'/)'
                    line = line.replace(CITE_RE.search(line).group(0),'('+'; '.join(cites)+')')
                line =line.replace(r'<ex></ex>', '')
                # write ex refs
                new_text.append(line)
        with open(os.path.join(dir2, file), 'w', encoding='utf8') as f2:
            f2.write(''.join(new_text))

