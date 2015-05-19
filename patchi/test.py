
import re

response = "[kappa]"
response = re.sub(r'\[\]\"', '', response)
#response = re.sub(r'\]', '', response)
#response = re.sub(r'\"', '', response)
print response