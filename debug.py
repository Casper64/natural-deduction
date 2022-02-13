from sre_constants import SUCCESS
from time import localtime, strftime

DEBUG=False

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

INFO=bcolors.OKCYAN
WARNING=bcolors.WARNING
ERROR=bcolors.FAIL
SUCCESS=bcolors.OKGREEN



def log(string: str, level=INFO, time=True):
    if not DEBUG:
        return
    t = ""

    if time:
        t = strftime("%H:%M:%S", localtime()) + " "
    print(f"{t}{level}{string}{bcolors.ENDC}")