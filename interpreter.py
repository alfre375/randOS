debugMode = True
import re, ast
import os
import randosUtils
import math as maths
#code = 'out(\';\');'
r = re.compile(r'''(['"])((?:\\.|(?!\1).)*)\1''')
c = re.compile(r'''^\s*([A-Za-z_][A-Za-z0-9_.]*)\s*\(([\s\S]*)\)\s*$''')
a = re.compile(r'''^\s*if\s+\(([\s\S]*)\)\s*{([\s\S]*)}\s*$''')
REGEX_LITERAL_LIST = re.compile(r'''^\s*\[([\s\S]*)\]\s*$''')
REGEX_WHILE = re.compile(r'''^\s*while\s+\(([\s\S]*)\)\s*{([\s\S]*)}$''')

def exactPath(relativePath: str, osPath: str):
    path: str = str(os.path.abspath(osPath + relativePath))
    if path.startswith(osPath):
        return path
    else:
        return False
    
def getSysDirFromRelative(relativePath: str, cwd: str, root: str) -> str | None:
    if not relativePath.startswith('/'):
        relativePath = cwd + '/' + relativePath
    relativePath = relativePath.replace('\\', '/')
    root = root.replace('\\', '/')
    absPath = os.path.abspath(root + '/' + relativePath)
    absPath.replace('\\', '/')
    if not absPath.startswith(root):
        return None
    absPath = absPath.removeprefix(root)
    if not absPath.startswith('/'):
        absPath = '/'
    return absPath

def debug(*msg: str):
    if debugMode:
        print('[DEBUG]', *msg)

class InvalidFunctionException(Exception):
    pass

class InterpretationInstance():
    def __init__(self, providedInformation: dict, filePerms: dict):
        self.variables: dict = {}
        self.functions: dict = {}
        self.classes: dict = {
            'str': {
                'variablesPublic': {},
                'functions': {
                    'toNumber': {
                        'takes': [{'name': 'inputString', 'type': 'str'}],
                        'code': {
                            'return parseNumber(inputString)'
                        }
                    }
                }
            }
        }
        self.providedInformation: dict = providedInformation
        self.filePerms: dict = filePerms
    
    def lex(self, code: str, separator: str = ';') -> list:
        chars: list = list(code)
        lines: list = []
        currentLine: str = ''
        isStringLiteral: int = 0
        isSpecialCharacter: bool = False
        wasSpecialCharacter: bool = False
        parenthesisLevel: int = 0
        curlyDepth: int = 0
        for char in chars:
            if (char == '{') and (not isStringLiteral):
                curlyDepth += 1
            elif (char == '}') and (not isStringLiteral):
                curlyDepth -= 1
            if curlyDepth > 0:
                currentLine += char
                continue
            #print(char, isStringLiteral, isSpecialCharacter, wasSpecialCharacter)
            if char == separator:
                if (isStringLiteral == 0) and (parenthesisLevel == 0):
                    lines.append(currentLine)
                    currentLine = ''
                    continue
            elif char == '\'':
                if (not isSpecialCharacter) and (isStringLiteral == 0):
                    isStringLiteral = 1
                elif (not isSpecialCharacter) and (isStringLiteral == 1):
                    isStringLiteral = 0
            elif char == '\\':
                if isSpecialCharacter and isStringLiteral:
                    isSpecialCharacter = False
                elif isStringLiteral:
                    isSpecialCharacter = True
            elif char == '"':
                if (not isSpecialCharacter) and (isStringLiteral == 0):
                    isStringLiteral = 2
                elif (not isSpecialCharacter) and (isStringLiteral == 2):
                    isStringLiteral = 0
            elif char == '(':
                if (not isSpecialCharacter):
                    parenthesisLevel += 1
            elif char == ')':
                if (not isSpecialCharacter):
                    parenthesisLevel -= 1
            currentLine += char
            if wasSpecialCharacter:
                isSpecialCharacter = False
                wasSpecialCharacter = False
            if isSpecialCharacter:
                wasSpecialCharacter = True
        if currentLine != '':
            lines.append(currentLine)
        return lines

    def run(self, line: str) -> None | str:
        line = line.strip()
        debug('RUNNING: ', line)
        f = re.match(r'declare ([a-zA-Z]+)\s*=\s*([\s\S]+)', line)
        if f:
            #print(f)
            varname = f.group(1)
            varval = f.group(2)
            varval = self.run(varval)
            vartype = None
            if isinstance(varval, str):
                vartype = 'str'
            elif isinstance(varval, bool):
                vartype = 'bool'
            elif isinstance(varval, float):
                vartype = 'number'
            elif isinstance(varval, list):
                vartype = 'list'
            self.variables[varname] = {'value': varval, 'type': vartype}
            return
        f = r.match(line)
        if f:
            #print(f)
            s = ast.literal_eval(f.group(0))
            return s
        f = c.match(line)
        if f:
            s = f.group(1)
            v = f.group(2)
            vsplit = self.lex(v, ',')
            vsplitcompiled = []
            for value in vsplit:
                vsplitcompiled.append(self.run(value))
            #print(s, v)
            #print(v, vsplit, vsplitcompiled)
            if s == 'out':
                vcompiled = self.run(v)
                print(vcompiled)
                return
            elif s == 'in':
                vcompiled = self.run(v)
                return input(vcompiled)
            elif s == 'equals':
                firstValue = vsplitcompiled[0]
                #print('<abx> ',firstValue)
                for val in vsplitcompiled:
                    #print('>abx< ',val)
                    if not (val == firstValue):
                        return False
                return True
            elif s == 'not':
                return not vsplitcompiled[0]
            elif s == 'getActiveDirectory':
                if not ('directoryInformation' in self.providedInformation['permissions']):
                    raise Exception('Permission directoryInformation is not in program metadata')
                return self.providedInformation['activeDirectory']
            elif s == 'writeToFile':
                filename: str = vsplitcompiled[0]
                textToWrite = vsplitcompiled[1]
                filepathExact = randosUtils.getExactLocation(filename, self.providedInformation['root'], self.providedInformation['activeDirectory'])
                
                if not filepathExact:
                    raise Exception('Invalid file location')
                
                filepathExact = filepathExact.replace('\\', '/')
                
                if not ('writeToFile' in self.providedInformation['permissions']):
                    raise Exception('Permission writeToFile is not in program metadata')
                
                if not filepathExact:
                    raise Exception('Invalid file location')
                
                if not os.path.exists(filepathExact):
                    dirnameList: list = filepathExact.split('/')
                    dirnameList.pop(len(dirnameList) - 1)
                    dirname: str = "/".join(dirnameList)
                    if dirname:
                        if (dirname.startswith(self.providedInformation['root'].replace('\\','/')) and os.path.exists(dirname)):
                            dirname = dirname.removeprefix(self.providedInformation['root'].replace('\\','/'))
                            if dirname == '':
                                dirname = '/'
                            print(self.providedInformation['root'])
                            print(dirname)
                            if randosUtils.hasPermission(self.providedInformation['userUUID'], 'w', dirname, self.filePerms):
                                with open(filepathExact, 'w') as file:
                                    file.write(textToWrite)
                                    file.close()
                                self.filePerms[filename] = {'owner': self.providedInformation['userUUID'], 'permissions': 'rw-------'}
                                randosUtils.updateFilePermsFile(self.filePerms)
                                filepathExact: str = randosUtils.getExactLocation(filename, self.providedInformation['root'], self.providedInformation['activeDirectory'])
                                return True
                            else:
                                return False
                        else:
                            raise Exception('Directory does not exist within simulated environment')
                    else:
                        raise Exception('No dirname')
                
                if not randosUtils.hasPermission(self.providedInformation['userUUID'], 'w', filename, self.filePerms):
                    return False
                
                with open(filepathExact, 'w') as file:
                    file.write(textToWrite)
                    file.close()
                
                return True
            elif s == 'readFromFile':
                fileToRead = vsplitcompiled[0]
                if not ('readFromFile' in self.providedInformation['permissions']):
                    raise Exception('Permission readFromFile is not in program metadata')
                
                filepathExact = randosUtils.getExactLocation(fileToRead, self.providedInformation['root'], self.providedInformation['activeDirectory'])
                
                if not filepathExact:
                    raise Exception('File does not exist within simulated environment')
                
                if not randosUtils.hasPermission(self.providedInformation['userUUID'], 'r', fileToRead, self.filePerms):
                    return False
                
                with open(filepathExact, 'r') as file:
                    if (isinstance(file, str)):
                        return file
                    else:
                        return file.read()
            elif s == 'changeActiveDirectory':
                directory: str = vsplitcompiled[0]
                directory = getSysDirFromRelative(directory, self.providedInformation['activeDirectory'], self.providedInformation['root'])
                if not directory:
                    raise Exception('Directory is outside of system')
                debug('Changing directory to ' + directory)
                while '//' in directory:
                    directory.replace('//', '/')
                directoryExact = randosUtils.getExactLocation(directory, self.providedInformation['root'], self.providedInformation['activeDirectory'])
                debug('Exact directory: ', directoryExact)
                if not randosUtils.hasPermission(self.providedInformation['userUUID'], 'r', directory, self.filePerms):
                    raise Exception('You do not have permission to access this directory')
                if directoryExact and os.path.exists(directoryExact):
                    self.providedInformation['activeDirectory'] = directoryExact.replace('\\','/').removeprefix(self.providedInformation['root'].replace('\\','/'))
                    if self.providedInformation['activeDirectory'] == '':
                        self.providedInformation['activeDirectory'] = '/'
                else:
                    raise Exception('Directory does not exist within simulated environment')
                return None
            elif s == 'or':
                for function_input in vsplitcompiled:
                    if function_input == True:
                        return True
                return False
            elif s == 'and':
                for function_input in vsplitcompiled:
                    if function_input == False:
                        return False
                return True
            elif s == 'getSplitCommand':
                if len(vsplitcompiled) == 0:
                    #print('No inputs, sending entire list')
                    return self.providedInformation['cmds']
                if (vsplitcompiled[0] < 0) or (vsplitcompiled[0] != float(maths.floor(vsplitcompiled[0]))):
                    raise Exception('Index must be a whole number (n >= 0 and n = roundDown(n))')
                #print('Input found, sending specific part')
                if (len(self.providedInformation['cmds']) - 1) < vsplitcompiled[0]:
                    return None
                return self.providedInformation['cmds'][int(vsplitcompiled[0])]
            elif s == 'strMerge':
                endStr = ''
                for val in vsplitcompiled:
                    endStr += val
                return endStr
            elif s == 'add':
                total = 0
                for val in vsplitcompiled:
                    if not type(val) == float:
                        raise TypeError('TypeError: cannot add a non-number value')
                    total += val
                return total
            elif s == 'isGreater':
                if len(vsplitcompiled) != 2:
                    raise Exception('Function can only compare exactly 2 numbers')
                if vsplitcompiled[0] > vsplitcompiled[1]:
                    return True
                return False
            elif s == 'isGreaterEq':
                if len(vsplitcompiled) != 2:
                    raise Exception('Function can only compare exactly 2 numbers')
                if vsplitcompiled[0] >= vsplitcompiled[1]:
                    return True
                return False
            elif s == 'strToNumber':
                if len(vsplitcompiled) != 1:
                    raise Exception(f'Function can only take one value, {len(vsplitcompiled)} values given')
                if type(vsplitcompiled[0]) != str:
                    raise TypeError('TypeError: strToNumber only takes a str value')
                return float(vsplitcompiled[0])
        f = REGEX_WHILE.match(line)
        if f:
            
            action = f.group(2)
            condition = True
            while True:
                if not condition:
                    break
                condition = f.group(1)
                if condition == '':
                    condition = 'true'
                condition = self.run(condition)
                debug('CONDITION: ', condition)
                if not condition:
                    break
                actions = self.lex(action)
                for actionsLine in actions:
                    debug('RUNNING: ', actionsLine)
                    if re.match(r'''^\s*continue\s*$''', actionsLine):
                        condition = False # stop further repeats of outer loop
                        break # break from inner loop
                    elif re.match(r'''^\s*break\s*$''', actionsLine):
                        break
                    elif re.match(r'''^\s*continue-if\s*\(([\s\S]*)\)\s*$''', actionsLine):
                        condition_inner = re.match(r'''^\s*continue-if\s*\(([\s\S]*)\)\s*$''', actionsLine).group(1)
                        condition_inner = self.run(condition_inner)
                        if condition_inner:
                            break # break from inner loop
                        else:
                            continue
                    elif re.match(r'''^\s*break-if\s*\(([\s\S]*)\)\s*$''', actionsLine):
                        debug('conditional break')
                        condition_inner = re.match(r'''^\s*break-if\s*\(([\s\S]*)\)\s*$''', actionsLine).group(1)
                        condition_inner = self.run(condition_inner)
                        if condition_inner:
                            condition = False # stop further repeats of outer loop
                            break # break from inner loop
                        else:
                            continue
                    self.run(actionsLine)
            return
        f = a.match(line)
        if f:
            condition = f.group(1)
            #print('> ', condition)
            ifTrue = f.group(2)
            ifTrueLexed = self.lex(ifTrue)
            #print(ifTrueLexed)
            condition = self.run(condition)
            #print('> ', condition)
            if condition:
                for itlLine in ifTrueLexed: # itl = ifTrueLexed
                    self.run(itlLine)
            #print(condition, ifTrue)
            return
        elif line in self.variables:
            return self.variables[line]['value']
        f = REGEX_LITERAL_LIST.match(line)
        if f:
            listContents: str = f.group(1)
            listValue: list = self.lex(listContents, ',')
            return listValue
        if line == 'true':
            return True
        if line == 'false':
            return False
        try:
            return float(line)
        except Exception:
            print('',end='')
        if line == 'none':
            return None
        if not line:
            return
        raise Exception(f'Invalid code {line}')

#interpreter = InterpretationInstance({ 'activeDirectory': '/' })
#lexed = interpreter.lex(code)
#print(lexed)
#for line in lexed:
#    interpreter.run(line)
#print(interpreter.variables)