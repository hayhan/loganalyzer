import re

file = open('./logs/tmp.txt', 'r')
newfile = open('./logs/tmp_new.txt', 'w')

# The pattern for the timestamp added by console tool
pattern0 = re.compile(r'\[(([01]\d|2[0-3]):([0-5]\d):([0-5]\d):(\d{3})|24:00:00:000)\]')
# The pattern for CM console prompts
pattern1 = re.compile('CM[/a-z-_ ]*> ', re.IGNORECASE)
# The pattern for the timestamp added by BFC
pattern2 = re.compile(r'\[(([01]\d|2[0-3]):([0-5]\d):([0-5]\d)|24:00:00) \d{2}/\d{2}/\d{4}\] ')
# The pattern for the timestamp added by others
pattern3 = re.compile(r'\d{2}/\d{2}/\d{4} (([01]\d|2[0-3]):([0-5]\d):([0-5]\d)|24:00:00) - ')

for line in file:
    """
    Remove the unwanted strings which include some kind of timestamps
    and console prompts.
    """
    newline0 = pattern0.sub('', line)
    #print(newline0, '')
    newline1 = pattern1.sub('', newline0)
    newline2 = pattern2.sub('', newline1)
    newline3 = pattern3.sub('', newline2)

    newfile.write(newline3)

file.close()
newfile.close()