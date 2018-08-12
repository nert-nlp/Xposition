import re, os

dir = 'markdown-and-macros'
dir2 = 'markdown-construals'

P_RE = re.compile('\[p(special [^\s\]]+)? [^\s\]]+ (?P<ss>[^\s\]]+)\]')
EXAMPLE_RE = re.compile('\[ex (?P<id>[^\s\]]+) (?P<ex>".+?")\]')


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
                # add to construals
                for ex in EXAMPLE_RE.finditer(line):
                    example = ex.group('ex')
                    # remove footnotes
                    example = re.sub('\[\^[0-9]+\]','',example)
                    ss = P_RE.search(example)
                    if not ss:
                        continue
                    ss = ss.group('ss')
                    ss = ss if '--' in ss else ss + '--' + ss
                    if ss not in construals:
                        construals[ss] = []
                    exref = '"[exref '+ex.group('id')+' '+file.replace('.txt', '')+']"'
                    id = '{0:03d}'.format(len(construals[ss])+1)
                    construals[ss].append('- [ex '+id+' '+example+' '+exref+']\n\n')

                tmp_ss = None

for ss in construals:
    print(ss)
    if ss.split('--')[0] == ss.split('--')[1]:
        construals[ss] = ['See '+'[ss '+ss.split('--')[0]+']'+'.\n\n'] + construals[ss]
    with open(os.path.join(dir2, ss+'.txt'), 'w', encoding='utf8') as f2:
            f2.write(''.join(construals[ss]))

