debugMode = False
import re, ast
import os
import randosUtils
import math as maths
import json
from pydub import AudioSegment
from pydub.playback import play
from pydub.generators import Sine
import struct
#code = 'out(\';\');'
REGEX_STRING = re.compile(r'''(['"])((?:\\.|(?!\1).)*)\1''')
c = re.compile(r'''^\s*([A-Za-z_][A-Za-z0-9_.]*)\s*\(([\s\S]*)\)\s*$''')
a = re.compile(r'''^\s*if\s+\(([\s\S]*)\)\s*{([\s\S]*)}\s*$''')
REGEX_LITERAL_LIST = re.compile(r'''^\s*\[([\s\S]*)\]\s*$''')
REGEX_WHILE = re.compile(r'''^\s*while\s+\(([\s\S]*)\)\s*{([\s\S]*)}\s*$''')
REGEX_FUNCTION_DECLARATION = re.compile(r'''^\s*fn\s+([a-zA-Z_]+)\s*\(([\sa-zA-Z_,:]*)\)\s*{([\s\S]*)}\s*$''')
REGEX_RETURN = re.compile(r'''^\s*return\s+([\s\S]*)''')

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
        
def numToStr(num: dict) -> dict:
    if num['class'] != 'number':
        raise TypeError('numToStr [INTERNAL FUNCTION] only accepts number')
    return {
        "class": "str",
        "variables": {
            "value": str(num['variables']['value'])
        }
    }

class InvalidFunctionException(Exception):
    pass

class InterpretationInstance():
    def __init__(self, providedInformation: dict, filePerms: dict):
        self.variables: dict = {}
        self.functions: dict = {}
        self.classes: dict = {
            'str': {
                'variablesStatic': {},
                'functionsStatic': {},
                'functions': {
                    'toNumber': {
                        "['str']": {
                            'takes': [{'name': 'inputString', 'type': 'str'}],
                            'code': {
                                'return parseNumber(inputString)'
                            }
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
        f = re.match(r'declare ([a-zA-Z_]+)\s*=\s*([\s\S]+)', line)
        if f:
            #print(f)
            varname = f.group(1)
            varval = f.group(2)
            varval = self.run(varval)
            """vartype = varval['class']
            varval = varval['variables']
            if isinstance(varval, str):
                vartype = 'str'
            elif isinstance(varval, bool):
                vartype = 'bool'
            elif isinstance(varval, float):
                vartype = 'number'
            elif isinstance(varval, list):
                vartype = 'list'"""
            self.variables[varname] = varval #{'value': varval, 'type': vartype}
            return
        f = REGEX_STRING.match(line)
        if f:
            #print(f)
            s = ast.literal_eval(f.group(0))
            return {
                "class": "str",
                "variables": {
                    "value": s
                }
            }
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
                if vcompiled['class'] != 'str':
                    if vcompiled['class'] == 'number':
                        vcompiled = numToStr(vcompiled)
                    else:
                        raise TypeError('out function accepts only str and num')
                print(vcompiled['variables']['value'])
                return
            elif s == 'in':
                vcompiled = self.run(v)
                if vcompiled['class'] != 'str':
                    if vcompiled['class'] == 'number':
                        vcompiled = numToStr(vcompiled)
                    else:
                        raise TypeError('in function accepts only str and num')
                return {
                    "class": "str",
                    "variables": {
                        "value": input(vcompiled['variables']['value'])
                    }
                }
            elif s == 'equals':
                firstValue = vsplitcompiled[0]
                #print('<abx> ',firstValue)
                for val in vsplitcompiled:
                    #print('>abx< ',val)
                    if not (val == firstValue):
                        return {
                            "class": "bool",
                            "variables": {
                                "value": False
                            }
                        }
                return {
                    "class": "bool",
                    "variables": {
                        "value": True
                    }
                }
            elif s == 'not':
                return {
                    "class": "bool",
                    "variables": {
                        "value": not vsplitcompiled[0]['variables']['value']
                    }
                }
            elif s == 'getActiveDirectory':
                if not ('directoryInformation' in self.providedInformation['permissions']):
                    raise Exception('Permission directoryInformation is not in program metadata')
                return {
                    "class": "str",
                    "variables": {
                        "value": self.providedInformation['activeDirectory']
                    }
                }
            elif s == 'writeToFile':
                if not (vsplitcompiled[0]['class'] == 'str'):
                    raise TypeError('Filename of writeToFile must be string')
                filename: str = vsplitcompiled[0]['variables']['value']
                if not (vsplitcompiled[1]['class'] == 'str'):
                    raise TypeError('File contents of writeToFile must be string')
                textToWrite = vsplitcompiled[1]['variables']['value']
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
                                return {
                                    "class": "bool",
                                    "variables": {
                                        "value": True
                                    }
                                }
                            else:
                                return {
                                    "class": "bool",
                                    "variables": {
                                        "value": False
                                    }
                                }
                        else:
                            raise Exception('Directory does not exist within simulated environment')
                    else:
                        raise Exception('No dirname')
                
                if not randosUtils.hasPermission(self.providedInformation['userUUID'], 'w', filename, self.filePerms):
                    return {
                        "class": "bool",
                        "variables": {
                            "value": False
                        }
                    }
                
                with open(filepathExact, 'w') as file:
                    file.write(textToWrite)
                    file.close()
                
                return {
                    "class": "bool",
                    "variables": {
                        "value": True
                    }
                }
            elif s == 'readFromFile':
                if not (vsplitcompiled[0]['class'] == 'str'):
                    raise TypeError('Filename must be string for readFromFile')
                fileToRead: str = vsplitcompiled[0]['variables']['value']
                if not ('readFromFile' in self.providedInformation['permissions']):
                    raise Exception('Permission readFromFile is not in program metadata')
                
                filepathExact = randosUtils.getExactLocation(fileToRead, self.providedInformation['root'], self.providedInformation['activeDirectory'])
                
                if not filepathExact:
                    raise Exception('File does not exist within simulated environment')
                
                if not randosUtils.hasPermission(self.providedInformation['userUUID'], 'r', fileToRead, self.filePerms):
                    return {
                        "class": "bool",
                        "variables": {
                            "value": False
                        }
                    }
                
                with open(filepathExact, 'r') as file:
                    if (isinstance(file, str)):
                        return {
                            "class": "str",
                            "variables": {
                                "value": file
                            }
                        }
                    else:
                        return {
                            "class": "str",
                            "variables": {
                                "value": file.read()
                            }
                        }
            elif s == 'changeActiveDirectory':
                if not (vsplitcompiled[0]['class'] == 'str'):
                    raise TypeError('Directory path must be str for changeActiveDirectory')
                directory: str = vsplitcompiled[0]['variables']['value']
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
                    if function_input['variables']['value'] == True:
                        return {
                            "class": "bool",
                            "variables": {
                                "value": True
                            }
                        }
                return {
                    "class": "bool",
                    "variables": {
                        "value": False
                    }
                }
            elif s == 'and':
                for function_input in vsplitcompiled:
                    if function_input['variables']['value'] == False:
                        return {
                            "class": "bool",
                            "variables": {
                                "value": False
                            }
                        }
                return {
                    "class": "bool",
                    "variables": {
                        "value": True
                    }
                }
            elif s == 'getSplitCommand':
                if len(vsplitcompiled) == 0:
                    #print('No inputs, sending entire list')
                    return {
                        "class": "list",
                        "variables": {
                            "value": self.providedInformation['cmds']
                        }
                    }
                if (vsplitcompiled[0]['class'] != 'number') or (vsplitcompiled[0]['variables']['value'] < 0) or (vsplitcompiled[0]['variables']['value'] != float(maths.floor(vsplitcompiled[0]['variables']['value']))):
                    raise Exception('Index must be a whole number (n >= 0 and n = roundDown(n))')
                #print('Input found, sending specific part')
                if (len(self.providedInformation['cmds']) - 1) < vsplitcompiled[0]['variables']['value']:
                    return None
                return {
                    "class": "str",
                    "variables": {
                        "value": self.providedInformation['cmds'][int(vsplitcompiled[0]['variables']['value'])]
                    }
                }
            elif s == 'strMerge':
                endStr = ''
                for val in vsplitcompiled:
                    if not (val['class'] == 'str'):
                        raise TypeError('strMerge accepts only str inputs')
                    endStr += val['variables']['value']
                return {
                    "class": "str",
                    "variables": {
                        "value": endStr
                    }
                }
            elif s == 'add':
                total = 0
                for val in vsplitcompiled:
                    if not (val['class'] == 'number'):
                        raise TypeError('TypeError: cannot add a non-number value')
                    total += val['variables']['value']
                return {
                    "class": "number",
                    "variables": {
                        "value": total
                    }
                }
            elif s == 'isGreater':
                if len(vsplitcompiled) != 2:
                    raise Exception('Function can only compare exactly 2 numbers')
                if (not (vsplitcompiled[0]['class'] == 'number')) or (not(vsplitcompiled[1]['class'] == 'number')):
                    raise TypeError('isGreater only accepts number values')
                if vsplitcompiled[0]['variables']['value'] > vsplitcompiled[1]['variables']['value']:
                    return {
                        "class": "bool",
                        "variables": {
                            "value": True
                        }
                    }
                return {
                    "class": "bool",
                    "variables": {
                        "value": False
                    }
                }
            elif s == 'isGreaterEq':
                if len(vsplitcompiled) != 2:
                    raise Exception('Function can only compare exactly 2 numbers')
                if (not (vsplitcompiled[0]['class'] == 'number')) or (not(vsplitcompiled[1]['class'] == 'number')):
                    raise TypeError('isGreater only accepts number values')
                if vsplitcompiled[0]['variables']['value'] >= vsplitcompiled[1]['variables']['value']:
                    return {
                        "class": "bool",
                        "variables": {
                            "value": True
                        }
                    }
                return {
                    "class": "bool",
                    "variables": {
                        "value": False
                    }
                }
            elif s == 'strToNumber':
                if len(vsplitcompiled) != 1:
                    raise Exception(f'Function can only take one value, {len(vsplitcompiled)} values given')
                if vsplitcompiled[0]['class'] != 'str':
                    raise TypeError('TypeError: strToNumber only takes a str value')
                return {
                    "class": "number",
                    "variables": {
                        "value": float(vsplitcompiled[0]['variables']['value'])
                    }
                }
            elif s == 'getAudioSegmentFromArray':
                if len(vsplitcompiled) != 1:
                    raise Exception(f'Function can only take one value, {len(vsplitcompiled)} values given')
                if vsplitcompiled[0]['class'] != 'list':
                    raise TypeError('TypeError: getAudioSegmentFromArray only takes a list value')
                audioSegment = AudioSegment(
                    data=b''.join(struct.pack('<h', sample) for sample in vsplitcompiled[0]['variables']['value']),
                    frame_rate=44100,
                    sample_width=2,
                    channels=1
                )
                return {
                    "class": "AudioSegment",
                    "variables": {
                        "value": audioSegment
                    }
                }
            elif s == 'getSineAudioAtFrequency':
                if len(vsplitcompiled) != 3:
                    raise Exception(f'Function can only take exactly 3 values, {len(vsplitcompiled)} values given')
                tone: AudioSegment = Sine(vsplitcompiled[0]['variables']['value']).to_audio_segment(vsplitcompiled[1]['variables']['value'], vsplitcompiled[2]['variables']['value'])
                return {
                    "class": "AudioSegment",
                    "variables": {
                        "value": tone
                    }
                }
            elif s == 'play':
                if len(vsplitcompiled) != 1:
                    raise Exception(f'Function can only take one value, {len(vsplitcompiled)} values given')
                if vsplitcompiled[0]['class'] != 'AudioSegment':
                    raise TypeError('TypeError: play only takes an AudioSegment value')
                play(vsplitcompiled[0]['variables']['value'])
                return
            
            # Custom functions
            fnp = self.lex(s, '.') # fnp = function name parts
            function_code = ''
            function_data_upper: dict = {}
            if len(fnp) == 1:
                debug('FNP is a root function')
                if not self.functions[fnp[0]]:
                    raise InvalidFunctionException(f'InvalidFunctionException: The function {fnp[0]} does not exist')
                function_data_upper = self.functions[fnp[0]]
            else:
                function_location: list = []
                if fnp[0] in self.classes:
                    function_location.append((self.functions[fnp[0]], 'class'))
                elif fnp[0] in self.variables:
                    function_location.append((self.variables[fnp[0]], 'variable'))
                else:
                    raise InvalidFunctionException(f'InvalidFunctionException: {fnp[0]} is neither a variable nor a class')
                for i in range(1, len(fnp)-1): # index 0 has already been done (see above)
                    current, current_type = function_location[i]
                    if current_type == 'class':
                        if i < len(fnp)-1:
                            if fnp[i] in current['variablesStatic']:
                                function_location.append((current['variablesStatic'][fnp[i]], 'variable'))
                            else:
                                raise InvalidFunctionException(f'InvalidFunctionException: {fnp[i]} is not a variable of {function_location}')
                        else:
                            if fnp[i] in current['functionsStatic']:
                                function_data_upper = current['functionsStatic'][fnp[i]]
                                break
                            else:
                                raise InvalidFunctionException(f'InvalidFunctionException: {fnp[i]} is not a function of {function_location}')
                    else:
                        raise Exception('This feature is not yet implemented')
            
            # Get function_data_lower
            varclasses = []
            for var in vsplitcompiled:
                varclasses.append(var['class'])
                
            function_data_lower: dict = {}
            if json.dumps(varclasses) in function_data_upper:
                function_data_lower = function_data_upper[json.dumps(varclasses)]
            elif '*' in function_data_upper:
                function_data_lower = function_data_upper['*']
            else:
                debug(f'ERROR: neither varclasses (value: {json.dumps(varclasses)}) nor "*" are in fdu (value: {function_data_upper})')
                raise InvalidFunctionException('Function does not exist with these variables')
            
            debug(f'function_data_lower: {function_data_lower}')
            function_lines = function_data_lower['code']
            debug(f'function_lines: {function_lines}')
            
            # Prepare an InterpretionInstance
            interpreter = InterpretationInstance(self.providedInformation, self.filePerms)
            interpreter.variables = self.variables
            interpreter.classes = self.classes
            interpreter.functions = self.functions
            
            # Get parameters of function
            i = 0
            function_variables: dict = {}
            for var in function_data_lower['variables']:
                varname = var[0]
                typeof = var[1]
                if vsplitcompiled[i]['class'] != typeof:
                    raise TypeError(f'Incorrect type (should be {typeof}, found {vsplitcompiled[i]['class']})')
                function_variables[varname] = vsplitcompiled[i]
                i += 1
            del i
            interpreter.variables.update(function_variables)
            
            returnValue = None
            for fline in function_lines:
                debug(f'RUNNING WITHIN FUNCTION: {fline}')
                res = interpreter.run(fline)
                debug(f'Response: {res}')
                if res and ('return' in res):
                    returnValue = res['return']
                    break
            
            # Update variable values as needed
            for var in self.variables:
                if not (var in interpreter.variables):
                    del self.variables[var]
                self.variables = interpreter.variables
            
            # Delete the interpreter of this function call and return
            del interpreter
            return returnValue
        
        f = REGEX_WHILE.match(line)
        if f:
            action = f.group(2)
            condition = {
                "class": "bool",
                "variables": {
                    "value": True
                }
            }
            while True:
                debug('CONDITION: ', condition)
                if not condition['variables']['value']:
                    break
                condition = f.group(1)
                if condition == '':
                    condition = 'true'
                condition = self.run(condition)
                debug('CONDITION: ', condition)
                if not condition['variables']['value']:
                    break
                actions = self.lex(action)
                for actionsLine in actions:
                    debug('RUNNING: ', actionsLine)
                    if re.match(r'''^\s*continue\s*$''', actionsLine):
                        break # break from inner loop
                    elif re.match(r'''^\s*break\s*$''', actionsLine):
                        condition = {
                            "class": "bool",
                            "variables": {
                                "value": False
                            }
                        } # stop further repeats of outer loop
                        break
                    elif re.match(r'''^\s*continue-if\s*\(([\s\S]*)\)\s*$''', actionsLine):
                        condition_inner = re.match(r'''^\s*continue-if\s*\(([\s\S]*)\)\s*$''', actionsLine).group(1)
                        condition_inner = self.run(condition_inner)
                        if condition_inner['variables']['value']:
                            break # break from inner loop
                        else:
                            continue
                    elif re.match(r'''^\s*break-if\s*\(([\s\S]*)\)\s*$''', actionsLine):
                        debug('conditional break')
                        condition_inner = re.match(r'''^\s*break-if\s*\(([\s\S]*)\)\s*$''', actionsLine).group(1)
                        condition_inner = self.run(condition_inner)
                        if condition_inner['variables']['value']:
                            condition = {
                                "class": "bool",
                                "variables": {
                                    "value": False
                                }
                            } # stop further repeats of outer loop
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
            if condition['variables']['value']:
                for itlLine in ifTrueLexed: # itl = ifTrueLexed
                    self.run(itlLine)
            #print(condition, ifTrue)
            return
        
        f = REGEX_FUNCTION_DECLARATION.match(line)
        if f:
            function_name = f.group(1)
            function_code = f.group(3)
            debug(f.group(2))
            function_taken_variables = self.lex(f.group(2), ',')
            variables = []
            for var in function_taken_variables:
                debug(var)
                if not re.match(r'''^\s*[a-zA-Z_]+\s*:\s*[a-zA-Z_]+\s*$''', var):
                    raise Exception('Invalid format for variables')
                varsplit = var.split(':')
                variables.append([varsplit[0].strip(), varsplit[1].strip()])
            variables_types = []
            for var in variables:
                variables_types.append(var[1])
            
            if not (function_name in self.functions):
                self.functions[function_name] = {}
                
            self.functions[function_name][json.dumps(variables_types)] = {
                'code': self.lex(function_code),
                'takes': variables_types,
                'variables': variables
            }
            return
        
        f = REGEX_RETURN.match(line)
        if f:
            returnValue = f.group(1)
            returnValue = self.run(returnValue)
            return {
                "return": returnValue
            }
        elif line == 'return':
            return { "return": None }
        if line in self.variables:
            return self.variables[line]
        f = REGEX_LITERAL_LIST.match(line)
        if f:
            listContents: str = f.group(1)
            listValue: list = self.lex(listContents, ',')
            return {
                "class": "list",
                "variables": {
                    "value": listValue
                }
            }
        if line == 'true':
            return {
                "class": "bool",
                "variables": {
                    "value": True
                }
            }
        if line == 'false':
            return {
                "class": "bool",
                "variables": {
                    "value": False
                }
            }
        try:
            return {
                "class": "number",
                "variables": {
                    "value": float(line)
                }
            }
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