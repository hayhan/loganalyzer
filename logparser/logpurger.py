import re

file = open('./logs/test.txt', 'r')
newfile = open('./logs/test_simple_new.txt', 'w')
pattern = re.compile('CM[/a-z-_ ]*> ', re.IGNORECASE)

for line in file:
    m = pattern.match(line)
    if m:
        #print(m.group(0), end='\n')
        #print(len(m.group(0)))
        newline = line.replace(m.group(0), '', 1)
        #print(newline, end='')
        newfile.write(newline)
    else:
        #print(line, end='')
        newfile.write(line)

file.close()
newfile.close()
