import re

file = open('./logs/test.txt', 'r')
newfile = open('./logs/test_simple_new.txt', 'w')
pattern1 = re.compile('CM[/a-z-_ ]*> ', re.IGNORECASE)
pattern2 = re.compile(r'\[(([01]\d|2[0-3]):([0-5]\d):([0-5]\d)|24:00:00) \d{2}/\d{2}/\d{4}\] ')
pattern3 = re.compile(r'\d{2}/\d{2}/\d{4} (([01]\d|2[0-3]):([0-5]\d):([0-5]\d)|24:00:00) - ')

for line in file:
    m1 = pattern1.match(line)
    if m1:
        #print(m1.group(0), end='\n')
        #print(len(m1.group(0)))
        newline1 = line.replace(m1.group(0), '', 1)
        #print(newline1, end='')
        #newfile.write(newline1)
    else:
        #print(line, end='')
        #newfile.write(line)
        newline1 = line

    m2 = pattern2.match(newline1)
    if m2:
        #print(m2.group(0), end='\n')
        newline2 = newline1.replace(m2.group(0), '', 1)
    else:
        #print("no match for pattern2")
        newline2 = newline1

    m3 = pattern3.match(newline2)
    if m3:
        #print(m3.group(0), end='\n')
        newline3 = newline2.replace(m3.group(0), '', 1)
        #print(newline3, end='')
    else:
        #print("no match for pattern3")
        newline3 = newline2

    newfile.write(newline3)

file.close()
newfile.close()
