import re
import debug

def cleanup(string: str):
    """Cleanup a string"""
    string = string.strip()
    if not string:
        return ""

    start = 0
    end = len(string)

    if string[0] == "(" and len(re.findall("\(", string)) != len(re.findall("\)", string)):
        start += 1
    if string[-1] == ")" and len(re.findall("\(", string)) != len(re.findall("\)", string)):
        end -= 1

    return string[start:end]