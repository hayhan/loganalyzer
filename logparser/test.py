import re
from datetime import datetime
import os

teststrin = re.sub(' +', '\\\\s+', "123 abc  ABC")

print(teststrin)

print(datetime.now())

currentfiledir = os.path.dirname(__file__)
print(currentfiledir)
parentddir = os.path.abspath(os.path.join(currentfiledir, os.path.pardir))
print(type(parentddir))