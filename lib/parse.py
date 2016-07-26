import re

regex = "^((http[s]?|ftp):\/)?\/?([^:\/\s]+)"
reg = re.compile(regex)

def find_domain_name(url):
    return reg.findall(url)[0][2]