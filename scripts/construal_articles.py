import re, os

dir = 'markdown-and-macros'
dir2 = 'markdown-construals'

NEW_SS_RE = re.compile('(- )?\[ss (?P<ss>[\w$`-]+)\]')
ALT_SE_RE = re.compile('\(\[ss (?P<ss>[\w$`-]+)\]\)')
ORDINARY_RE = re.compile('^\s*[^-\s].*')
EXAMPLE_RE = re.compile("\[ex (?P<id>\w+) (?P<ex>'.+')\]")

construals = {}


if not os.path.exists(dir2):
    os.makedirs(dir2)

for file in os.listdir(dir):
    if file.endswith('.txt'):
        with open(os.path.join(dir,file), 'r', encoding='utf8') as f:


            default_ss = file.replace('.txt', '')
            tmp_ss = None

            print(default_ss)
            for line in f:
                if NEW_SS_RE.match(line):
                    default_ss = NEW_SS_RE.match(line).group('ss')
                elif ORDINARY_RE.match(line):
                    default_ss = file.replace('.txt', '')
                elif ALT_SE_RE.search(line):
                    tmp_ss = ALT_SE_RE.search(line).group('ss')
                elif '**'+file.replace('.txt', '')+'**' in line:
                    tmp_ss = file.replace('.txt', '')
                # add to construals
                ss = tmp_ss if tmp_ss else default_ss
                ss = ss if '--' in ss else ss+'--'+ss
                for ex in EXAMPLE_RE.finditer(line):
                    if ss not in construals:
                        construals[ss] = []
                    exref = '\'[exref '+ex.group('id')+' '+file.replace('.txt', '')+']\''
                    id = '{0:03d}'.format(len(construals[ss])+1)
                    construals[ss].append('- [ex '+id+' '+ex.group('ex')+' '+exref+']\n\n')

                tmp_ss = None

for ss in construals:
    print(ss)
    if ss.split('--')[0] == ss.split('--')[1]:
        construals[ss] = ['See '+'[ss '+ss.split('--')[0]+']'+'.\n\n'] + construals[ss]
    with open(os.path.join(dir2, ss+'.txt'), 'w', encoding='utf8') as f2:
            f2.write(''.join(construals[ss]))

