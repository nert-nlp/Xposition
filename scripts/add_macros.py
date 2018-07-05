import re, os

dir = 'markdown'
dir2 = 'markdown-and-macros'

P_RE = re.compile(r'\[([\w\\\'-])+\]\(/en/(?P<p>[\w\'\\-]+)\)')
SS_RE = re.compile(r'\[[\w$`-]+\]\(/(?P<ss>[\w$`-]+)\)')
NEW_SS_RE = re.compile('(- )?\[[\w$`-]+\]\(/(?P<ss>[\w$`-]+)\)')
ALT_SE_RE = re.compile('\(\[[\w$`-]+\]\(/(?P<ss>[\w$`-]+)\)\)')
ORDINARY_RE = re.compile('^\s*[^-\s].*')
EXAMPLE_RE = re.compile('- (<a id="ex(?P<id>\w+)"></a>)?"<i>(?P<ex>.+)</i>"')
EX_REF_RE = re.compile('\[[\w .,-]+?\]\(/(?P<ss>[\w$`-]+)/#ex(?P<id>\w+)\)')

ids = {}

if not os.path.exists(dir2):
    os.makedirs(dir2)

for file in os.listdir(dir):
    if file.endswith('.txt'):
        with open(os.path.join(dir,file), 'r', encoding='utf8') as f:
            new_text = []


            default_ss = file.replace('.txt', '')
            tmp_ss = None
            id_index = 1

            print(default_ss)
            for line in f:
                # fix Part/Portion
                line = line.replace('Part/Portion', 'PartPortion')

                if NEW_SS_RE.match(line):
                    default_ss = NEW_SS_RE.match(line).group('ss')
                elif ORDINARY_RE.match(line):
                    default_ss = file.replace('.txt', '')
                elif ALT_SE_RE.search(line):
                    tmp_ss = ALT_SE_RE.search(line).group('ss')
                elif '**'+file.replace('.txt', '')+'**' in line:
                    tmp_ss = file.replace('.txt', '')
                # convert p
                for p_link in P_RE.finditer(line):
                    prep = p_link.group('p')
                    if ORDINARY_RE.match(line):
                        line = line.replace(p_link.group(0), '[p en/' + prep + ']')
                    else:
                        line = line.replace(p_link.group(0), '[p en/'+prep+' '+(tmp_ss if tmp_ss else default_ss)+']')
                # convert ss
                for ss_link in SS_RE.finditer(line):
                    ss = ss_link.group('ss')
                    line = line.replace(ss_link.group(0), '[ss '+ss+']')
                # convert examples
                for example in EXAMPLE_RE.finditer(line):
                    ex = example.group('ex').replace("'",r"\'").replace("\\","\\\\")
                    ex = ex.replace('"','')
                    ex = ex.replace('<i>','').replace('</i>','')
                    ex = ex.replace('</i>','')
                    id = example.group('id')
                    if not id:
                        id = str(id_index)+'?'
                    ids[id] = id_index
                    line = line.replace(example.group(0), '- [ex '+'{0:03d}'.format(id_index)+' '+'\''+ex+'\''+']')
                    id_index += 1
                # fix various junk
                if re.match(r'^{?[0-9]*}?$', line.strip()):
                    line = '\n'
                line = line.replace(r'\_','_')
                line = line.replace('{}','')
                line = line.replace('](', '] (')
                line = line.replace(r'\ex', '')
                line = line.replace(r'    - [ex', '- [ex')

                tmp_ss = None
                new_text.append(line)

            with open(os.path.join(dir2, file), 'w+', encoding='utf8') as f2:
                f2.write(''.join(new_text))

for file in os.listdir(dir2):
    if file.endswith('.txt'):
        with open(os.path.join(dir2, file), 'r', encoding='utf8') as f:
            new_text = []
            for i, line in enumerate(f):
                # convert example refs
                for ex_link in EX_REF_RE.finditer(line):
                    ss = ex_link.group('ss')
                    id = ex_link.group('id')
                    if id in ids:
                        line = line.replace(ex_link.group(0), '[exref ' + '{0:03d}'.format(ids[id]) + ' ' + ss + ']')
                    else:
                        line = line.replace(ex_link.group(0), '[exref ' + '???' + ' ' + ss + ']')
                        print('fix exref', file, id, ss)
                new_text.append(line)
        with open(os.path.join(dir2, file), 'w', encoding='utf8') as f2:
            f2.write(''.join(new_text))

