from tkinter import N
import debug
import util
import re
from tokens import Token, TokenState
from copy import deepcopy

operator_regex = r"\^|v|->|=|^!$"

class Parser:
    def __init__(self, premise: str, raw=None):
        self.premise = util.cleanup(premise)

        if raw:
            self.raw = raw
        else:
            self.raw = self._parse()
        self.literals = self.get_literals()
        self.tokens = TokenState(premise)
        self._tokenize(self.raw, 0)

    def get_literals(self):
        """Get all the literals from the premise"""
        self.literals = []
        # Loop over multidimensional array and check if the partial is not an operator
        # so it must be a literal
        def loop(raw):
            if isinstance(raw, list):
                for partial in raw:
                    loop(partial)
            elif not re.match(operator_regex, raw):
                self.literals.append(raw)

        loop(self.raw)
        return self.literals

    def _parse(self):
        result = self._parse_parentheses(self.premise)
        self._parse_operators(result, result, 0)
        self._cleanup(result, result, 0)
        result = self._check(result)
        return result

    def _check(self, a, level=0):
        if isinstance(a, list) and len(a) == 1:
            a = a[0]
            a = self._check(a, 0)
        elif isinstance(a, list):
            for i in range(len(a)):
                a[i] = self._check(a[i], level+1)
        # elif level == 0:
        #     return a
        # Only case where a is a string and should not be wrapped in a list
        elif not isinstance(a, list) and a != '!' and level == 0:
            return [a]
        return a

    def _parse_parentheses(self, string: str):
        """Returns the premise in a multidimensional array according to the parentheses"""
        result = []
        stack = []
        start = 0
        
        # Extract all the parentheses into a multidimensional array
        # Loop through all the characters and detect if there are parentheses
        # If so add their contents on a stack, useful when dealing with nested parentheses
        for i, c in enumerate(string):
            if c == '(':
                # TODO: maybe change this to 'if not stack and ...'
                if not stack and (res := string[start:i]):
                        result.append(res)
                elif res := string[start + 1:i]:
                    stack[len(stack)-1].append(res)
                start = i
                stack.append([])
            elif c == ')' and stack:
                prev = stack.pop()
                if rest := string[start + 1:i]:
                    prev.append(rest)
                if not stack:
                    result.append(prev)
                else:
                    stack[len(stack)-1].append(prev)
                start = i + 1
            elif c == ')':
                debug.log(f"Missing '(' in '{string}'", debug.WARNING)
        
        if stack:
            debug.log(f"Missing ')' in '{string}'", debug.WARNING)


        # In case that the premise doesn't end with an ')', but does contain parentheses
        if result and string[start + 1:]:
            result.append(string[start + 1:])
        # If the result is nothing at this point, it means that there are no parentheses
        if len(result) == 0:
            result = [string]
        # Remove the structure unnecessary parentheses created e.g. ((p ^ q)) creates [['p ^ q']]
        # But should be ['p ^ q']
        # Choose tho do it here instead of on the string,
        # because it's easier to implement when the structure is already clear

        return self._check(result)

    def _parse_operators(self, result: any, original: list, index: int):
        """Parse the operators from the array given from `Parser._parse_parentheses`"""
        # Find the operators and splice them accordingly:
        # ['a -> b'] becomes ['a', '->', 'b']
        if isinstance(result, list):
            i = 0
            while i < len(result):
                i += self._parse_operators(result[i], result, i)
                i += 1
            return 0
        else:
            # variable to keep track how many replaces are done
            l =  0
            split = False
            while match := re.search(operator_regex, result, re.MULTILINE):
                # If the operator is the not operator wrap it in "parentheses", so the main operator gets preserved in the case
                # !(p ^ q) -> r     = [[!, [p, ^, q]], ->, s]
                if match.group() == "!":
                    end = original[index+1]
                    new_list = [original[index], end]
                    n = self._parse_operators(end, new_list, 1)
                    original[index:index+2] = [new_list]
                    index += 1
                    # Don't know if there are any cases where there should be string left after the ! operator
                    if len(original) > 1:
                        result = original[index]
                    else:
                        result = ""
                # Replacing magic for multiple operators with regex's
                elif split:
                    end = result[match.end():]
                    # Case of chained operators e.g. p ^ q ^ r will become [p, ^, [q, ^, [r]]]
                    # This implementrs a fix where the last chained operator is not inside of a list, but placed outside
                    # So p ^ q ^ r will become [p, ^, [q, ^, r]]
                    if len(end) <= 2:
                        new_list = [result[:match.start()], result[match.start():match.end()], end]
                        n = self._parse_operators(end, new_list, 2)
                        original[index] = new_list
                    else:
                        new_list = [result[:match.start()], result[match.start():match.end()], [end]]
                        original[index:index+1] = [new_list]
                        n = self._parse_operators(new_list, original, 2)

                    index += 1
                    l += 1
                    # For cases where there is are parentheses in the middle of the string
                    #  a ^ d ^ (b ^ c) ^ e will become ['a', '^', ['d', '^', ['b', '^', 'c']], '^', 'e'] when first parsed.
                    # But will be converted another time correctly by 'Token.get_raw' into  a ^ ((d ^ b ^ c) ^ e)
                    if len(original) > index:
                        new_list = deepcopy(original[index-1])
                        end = deepcopy(original[index])
                        new_list[2] = end
                        n = self._parse_operators(end, new_list, 2)
                        original[index-1] = new_list

                    result = ""
                # Replacing magic with regex's
                else:
                    original[index:index] = [result[:match.start()], result[match.start():match.end()]]
                    l += 2
                    index += 2

                    split = True
                    result = result[match.end():]
            original[index:index+1] = [result]
            return l

    def _cleanup(self, original, result: list, index: int):
        """Cleanup the array from `Parser._parse_operators`"""
        # Delete all empty values from the list
        if isinstance(result, list):
            i = 0
            while i < len(result):
                i += self._cleanup(result, result[i], i)
                i += 1
            return 0
        else:
            result = util.cleanup(result)
            # Delete the index if its value is empty
            if not result:
                del original[index]
                return - 1
            else:
                original[index] = result
            return 0

    def _tokenize(self, raw: list, depth: int):
        """Convert the raw state into tokens"""
        for index, partial in enumerate(raw):
            if isinstance(partial, str) and re.match(operator_regex, partial, re.MULTILINE):
                # An operator has a righthand side and lefthand side, IF the operator is not not ('!')
                operator = partial
                lh=""
                if operator != '!':
                    lh = raw[index-1]
                rh = raw[index+1]
                token = Token(lh, operator, rh, depth)
                self.tokens.append(token)
        for index, partial in enumerate(raw):
            if isinstance(partial, list):
                self._tokenize(partial, depth+1)
        
                
        