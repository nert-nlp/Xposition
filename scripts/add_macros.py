# coding=utf-8
import re, os

dir = 'markdown'
dir2 = 'markdown-and-macros'


P_RE = re.compile(r'\[(?P<text>([\w\\\'’-])+)\]\(/en/(?P<p>[\w\'’\\-]+)\)')
SS_RE = re.compile(r'\[[\w$`-]+\]\(/(?P<ss>[\w$`-]+)\)')
HEADER_RE1 = re.compile('^(- )?(<(ex|sn)>)?('+SS_RE.pattern+'.*):(</(ex|sn)>)?$') # [PartPortion](/PartPortion) is used ...:
HEADER_RE2 = re.compile('^(- )?(<(ex|sn)>)?(.*'+SS_RE.pattern+'):(</(ex|sn)>)?$') # [PartPortion](/PartPortion) is used ...:
HEADER_RE3 = re.compile('^(- )?(<(ex|sn)>)?(.*: '+SS_RE.pattern+')(</(ex|sn)>)?$') # [PartPortion](/PartPortion) is used ...:
TABLE_HEADER_RE = re.compile('(<(ex|sn)>)?'+SS_RE.pattern+'(</(ex|sn)>)?\|')
ALT_SS_RE = re.compile('\('+SS_RE.pattern+'(: .+)?\)')
SUBSCRIPT_SS_RE = re.compile('<sub>'+SS_RE.pattern+'</sub>')
ORDINARY_RE = re.compile('^(\[|\w).*$')
EXAMPLE_RE = re.compile('<(ex|sn)>(?P<ex>.+?)</(ex|sn)>')
LABEL_RE = re.compile('<label>(?P<label>.+?)</label>')
REF_RE = re.compile('<(ref)>(?P<label>.+?)</(ref)>')

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
        line = line.replace('_ ', r'\_ ')
        line = line.replace(' _', r' \_')
        line = re.sub(r']_(?=\w)', r']\_', line)
        line = re.sub(r'(?<=\w)_\[', r'\_[', line)

        for example in EXAMPLE_RE.finditer(line):
            ex = example.group('ex').replace('"', r'\"').replace("\\", "\\\\").strip()
            if not re.search('\w',ex):
                line = line.replace(example.group(0),'')
                continue
            if not re.search(r'\[p(special [\w\'’\\-]+)? \w\w/[\w\'’\\-]+( [\w$`-]+)?\]',ex):
                line = line.replace(example.group(0), ex)
                continue
            line = line.replace(example.group(0), '[ex ' + str(self.INDEX).zfill(3) + ' ' + '"' + ex + '"' + ']')
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

            line = line.replace(ex_link.group(0), ', '.join(repl))
        return line

def check_brackets(text):
    depth = 0
    for ch in text[:-1]:
        if ch == '[': depth+=1
        elif ch == ']': depth-=1
        if depth == 0: return False
    if text[-1] == ']' and depth==1: return True
    else: return False



if not os.path.exists(dir2):
    os.makedirs(dir2)

examples = Examples()

for file in os.listdir(dir):
    if file.endswith('.txt'):
        with open(os.path.join(dir,file), 'r', encoding='utf8') as f:
            new_text = []


            title = file.replace('.txt', '').replace(' ','_')
            default_ss = title
            table_ss = []
            tmp_ss = None
            previous_depth = 0
            depth = 0

            examples.INDEX = 1
            lines = f.readlines()
            for index, line in enumerate(lines):
                # fix Part/Portion
                line = line.replace('Part/Portion', 'PartPortion')

                depth = len(re.match('^\t*', line).group()) if line.strip() else depth

                if HEADER_RE1.match(line) or HEADER_RE2.match(line) or HEADER_RE3.match(line):
                    default_ss = SS_RE.search(line).group('ss')
                    # print(default_ss,line)
                elif TABLE_HEADER_RE.search(line):
                    table_ss = []
                    for ss in SS_RE.finditer(line):
                        table_ss.append(ss.group('ss'))
                elif ORDINARY_RE.match(line) or depth < previous_depth:
                    default_ss = title
                    # print(default_ss, line)

                # convert p
                ignore_usage = False
                while P_RE.search(line):
                    p_link = P_RE.search(line)

                    if ALT_SS_RE.search(line):
                        tmp_ss = ALT_SS_RE.search(line).group('ss')
                        # print(ALT_SS_RE.search(line).group(), tmp_ss)
                    elif '**' + file.replace('.txt', '') + '**' in line:
                        tmp_ss = title
                        # print(tmp_ss, line)
                    if not '|' in line:
                        table_ss = []

                    prep = p_link.group('p')
                    prep = re.sub('[’`]',"'",prep)
                    text = p_link.group('text')
                    text = re.sub('[’`]', "'", text)
                    if '|' in line and len(table_ss) == 2:
                        tmp_ss = table_ss[0 if p_link.start()<line.index('|') else 1]
                    for x in SUBSCRIPT_SS_RE.finditer(line):
                        if p_link.end() == x.start():
                            tmp_ss = x.group('ss')
                            break
                    # no usage for prep in brackets
                    for i,ch in enumerate(line):
                        if not ch == '[': continue
                        for j, ch2 in enumerate(line[i:]):
                            if ch=='[' and ch2==']':
                                start = i
                                end = i+j
                                x = line[start:end+1]
                                if p_link.start()>start and p_link.end()<end and check_brackets(x):
                                    ignore_usage = True
                                    break
                        if ignore_usage: break
                    if ' ' in default_ss:
                        ignore_usage = True
                    # examples with readings don't get a usage
                    if EXAMPLE_RE.search(line) and len(lines)>index+1:
                        next_line = lines[index + 1]
                        i = 1
                        while next_line.strip()=='' and len(lines)>index+i:
                            next_line = lines[index + i]
                            i +=1
                        if not EXAMPLE_RE.search(next_line) and re.search(r'[Rr]eading', next_line):
                            ignore_usage = True
                    pstart = '[p'
                    if not text == prep:
                        pstart = '[pspecial ' + text
                    if EXAMPLE_RE.search(line) and not ignore_usage:
                        line = line.replace(p_link.group(0),
                                            pstart + ' en/' + prep + ' ' + (tmp_ss if tmp_ss else default_ss) + ']', 1)
                    else:
                        line = line.replace(p_link.group(0), pstart + ' en/' + prep + ']', 1)

                    ignore_usage = False
                    tmp_ss = None

                # convert ss
                for ss_link in SS_RE.finditer(line):
                    ss = ss_link.group('ss')
                    line = line.replace(ss_link.group(0), '[ss '+ss+']')
                # add labels
                if LABEL_RE.search(line):
                    examples.add_label_id(LABEL_RE.search(line).group('label'), title)
                    line = LABEL_RE.sub('', line)
                    line = line.replace(r'<ex></ex>', '')
                    if not re.search('\w',line):
                        line = ''
                # convert examples
                line = examples.convert_example(line)
                if re.match('[}{]',line.strip()):
                    line = '\n'


                previous_depth = depth
                new_text.append(line)
            if not ' ' in file:  # ignore 'Special Constructions', ...
                with open(os.path.join(dir2, file), 'w+', encoding='utf8') as f2:
                    f2.write(''.join(new_text))


for file in os.listdir(dir2):
    if file.endswith('.txt'):
        with open(os.path.join(dir2, file), 'r', encoding='utf8') as f:
            new_text = []

            for i, line in enumerate(f):

                # fix whitespace
                if new_text and line.strip() == '' and new_text[-1].strip() == '':
                    new_text.pop()

                # convert example refs
                line = examples.convert_ex_ref(line, file.replace('.txt',''))
                # misc
                line =line.replace(r'<ex></ex>', '')
                while re.search(r'\[\[`[A-Za-z$]\]\]', line):
                    x = re.search(r'\[\[(?P<ss>`[A-Za-z$])\]\]', line)
                    line = line.replace(x.group(0), '[ss '+x.group('ss')+']')

                new_text.append(line)


        if not ' ' in file:  # ignore 'Special Constructions', ...
            with open(os.path.join(dir2, file), 'w', encoding='utf8') as f2:
                f2.write(''.join(new_text))

