import re, ast
import os
import randosUtils
#code = 'out(\';\');'
r = re.compile(r'''(['"])((?:\\.|(?!\1).)*)\1''')
c = re.compile(r'''^\s*([A-Za-z_][A-Za-z0-9_.]*)\s*\(([\s\S]*)\)\s*$''')
a = re.compile(r'''^\s*if\s+\(([\s\S]*)\)\s*{([\s\S]*)}\s*$''')

def exactPath(relativePath: str, osPath: str):
    path: str = str(os.path.abspath(osPath + relativePath))
    if path.startswith(osPath):
        return path
    else:
        return False

class InvalidFunctionException(Exception):
    pass

class InterpretationInstance():
    def __init__(self, providedInformation: dict, filePerms: dict):
        self.variables: dict = {}
        self.providedInformation: dict = providedInformation
        self.filePerms: dict = filePerms
    
    def lex(self, code: str, separator: str = ';') -> list:
        chars: list = list(code)
        lines: list = []
        currentLine: str = ''
        isStringLiteral: int = 0
        isSpecialCharacter: bool = False
        wasSpecialCharacter: bool = False
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
                if isStringLiteral == 0:
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
        #print(line)
        f = re.match(r'declare ([a-zA-Z]+)\s*=\s*([\s\S]+)', line)
        if f:
            #print(f)
            varname = f.group(1)
            varval = f.group(2)
            varval = self.run(varval)
            self.variables[varname] = varval
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
        f = a.match(line)
        if f:
            condition = f.group(1)
            #print('> ',condition)
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
            return self.variables[line]
        if line == 'true':
            return True
        if line == 'false':
            return False
        raise Exception(f'Invalid code {line}')

#interpreter = InterpretationInstance({ 'activeDirectory': '/' })
#lexed = interpreter.lex(code)
#print(lexed)
#for line in lexed:
#    interpreter.run(line)
#print(interpreter.variables)