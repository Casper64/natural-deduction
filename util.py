import re
import debug

def cleanup(string: str):
    """Cleanup a string"""
    string = string.strip()
    if not string:
        return ""
    
    if string[0] != "!" and string[-1] == ')' and len(re.findall('\)', string)) == 1:
        string = string[:-1]
    if string[0] == '(' and len(re.findall('\(', string)) == 1:
        string = string[1:]
    
    return string