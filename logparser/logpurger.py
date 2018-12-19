import re

file = open('./logs/test.txt', 'r')
newfile = open('./logs/test_new.txt', 'w')
pattern1 = re.compile('CM[/a-z-_ ]*> ', re.IGNORECASE)
pattern2 = re.compile(r'\[(([01]\d|2[0-3]):([0-5]\d):([0-5]\d)|24:00:00) \d{2}/\d{2}/\d{4}\] ')
pattern3 = re.compile(r'\d{2}/\d{2}/\d{4} (([01]\d|2[0-3]):([0-5]\d):([0-5]\d)|24:00:00) - ')

for line in file:
    newline1 = pattern1.sub('', line)
    newline2 = pattern2.sub('', newline1)
    newline3 = pattern3.sub('', newline2)

    newfile.write(newline3)

file.close()
newfile.close()