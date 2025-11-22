# Important functions (written in python)
## out(text: str)
Returns: None\
This function prints a value to the console

## in(text: str)
Returns: The inputted text (str)\
This function prints text to the screen, then gives the user an opportunity to enter text, then returns the text when the user presses the return key

## equals(input...)
Returns: Whether all inputs are equal to eachother (bool)\
This function takes an unlimited number of inputs and returns true if all inputs are equal and false otherwise

## not(input: bool)
Returns: The opposite of input (bool)\
If true is given as an input, the function returns false, and if false is given as an input, the function returns true

## getActiveDirectory()
Returns: The current working directory (str)\
Required permissions: directoryInformation
This function takes no inputs and returns the current working directory

## writeToFile(filename: str, textToWrite: str)
Returns: Whether the operation was successful (bool)\
Required permissions: writeToFile\
This function will, providing the necessary permissions are met (for existing files: user executing command must have write permission of the existing file; for new files: user executing command must have write permission of the directory in which to create the file), write to a file with the name in filename the text in textToWrite, creating the file if it doesn't exist. IMPORTANT NOTE: an exception is raised if neither the file nor the directory in which the file is meant to be created in exist.

## readFromFile(fileToRead: str)
Returns: Contents of the file (str)\
Required permissions: readFromFile\
This function will read the contents of the file, so long as the user has read permissions for the file. If the file is not found, an exception will be raised. If the file is found but the user does not have read permissions, the function returns false.

## changeActiveDirectory(directory: str)
Returns: none\
This function changes the active directory of the user. It raises an exception if the directory does not exist within the simulated environment, or if the directory does exist but the user does not have read permissions for the directory specified.

## or(booleanValue...: bool)
Returns: Whether at least one of the inputted booleanValue values are true (bool)\
Iterates over booleanValue, and if none are true, returns false, otherwise, returns true

## and(booleanValue...: bool)
Returns: Whether all of the inputted booleanValue values are true (bool)\
Iterates over booleanValue, and if none are false, returns true, otherwise, returns false

## getSplitCommand(index: number | none)
Returns: The entered command separated by spaces into a list, at the specified index if specified, or the entire list otherwise\
If a valid index (index must be a whole number) is specified, the function returns the item of the comma-separated command list at the specified index. If no index is specified, the functionr returns the entire comma-separated command list. If an invalid index is specified, the command raises an exception. Returns none if the index is valid but is not within the comma-separated command list.

## strMerge(strings...: str)
Returns: All the strings combined in the order they are passed (str)\
Merges all the strings provided in order without any separator in between

## add(numbers...: number)
Returns: The sum of all numbers passed (number)\
Adds together all numbers passed. Raises exception if a value that is passed is not of type `number`.

## isGreater(number_a: number, number_b: number)
Returns: Whether number_a is greater than number_b (bool)\
If `number_a > number_b`, returns `true`. Otherwise, returns `false`. If both numbers are equal, this function will return `false`. If this is not the desired result, see `isGreaterEq`.

## isGreaterEq(number_a: number, number_b: number)
Returns: Whether number_a is greater than or equal to number_b (bool)\
If `number_a >= number_b`, returns `true`. Otherwise, returns `false`. If both numbers are equal, this function will return `true`. If this is not the desired result, see `isGreater`.

## strToNumber(string: str)
Returns: A number of the provided string (number)\
The function returns a number based on the provided string. Function will raise an error if a value other than a string is provided.

## getAudioSegmentFromArray(array: list)
Returns: The audio segment (AudioSegment)\
The function returns an audio segment formed from the array

## getSineAudioAtFrequency(frequency: number, duration: number, volume: number)
Returns: The audio segment (AudioSegment)\
The function returns an audio segment at the given frequency for the specified duration at the specified volume

## getAudioSegmentFromWavFile(filename: str)
Returns: An audio segment from the wav file (AudioSegment), or if the user does not have permission to access the file, returns false\
Required permissions: readFromFile\
The function will get an audio segment from the specified file

## play(audio_segment: AudioSegment)
Returns: none\
The function plays the given audio segment

## multiply(values...: number)
Returns: All values multiplied together (number)\
All values get multiplied together

## exponent(val1: number, val2: number)
Returns: val1 to the power of val2 (number)\
One number to the power of another

## sin(val: number)
Returns: sine of val (number)\
Returns the sine of val (val should be radian)

## randNumBetween(low: number, high: number)
Returns: A random number between the low number and the high number (number)\
Returns a random number (includes decimals) between the low and high number. If you want an integer, combine the function with floor()

## getCurrentTimestamp()
Returns: The number of ms since epoch (number)\
Required permissions: readCurrentTime\
Returns the number of milliseconds since epoch, which is 1 Jan 1970 at 00h00m00

## floor(val: number)
Returns: The number resulting from rounding val down (number)\
Returns val rounded down

# Important functions (written in ROSC)
## divide(val1: number, val2: number)
Returns: val1 divided by val2 (number)\
Division function to divide one number (val1) by another (val2)

# General Syntax
## Variables
These are simple. Variables are declared as follows: `declare {VARIABLE_NAME} = {VALUE};`. Their names should follow the regex `[a-zA-Z_]+`

## Conditional Statements
Conditional statements are denoted in RandOSCode as follows:
```
if ({CONDITION}) {
    {IF TRUE}
};
```
Conditions must be enclosed in parenthesis, if trues must be enclosed in curly brackets

## Semicolons
At the end of every instruction in ROSC, there must be a semicolon. This includes variable declarations, any functions except those in conditions of if statements, and conditional statements.

## Loops
Loops can be declared as follows:
```
while ({CONDITION}) {
    {IF TRUE}
};
```
If no condition is specified (note: even if no condition is specified, the parenthesis are still required), it will repeat until the `break;` command is given. Within these loops, you can use the `break;` command to exit the loop, and the `continue;` command to skip to the next iteration of the loop. Similarly, the `break-if ({CONDITION});` command exits the loop iff the condition is true, and the `continue-if ({CONDITION});` command skips to the next iteration of the loop iff the condition is true. However, as of right now, these functions (break, break-if, continue, and continue-if) only work at the base of the loop — that is, they do not work inside of if statements.

## Functions
Functions can be declared as follows:
```
fn {FUNCTION_NAME}({VARNAME: VARTYPE}) {
    {CONTENTS}
};
```
New variables made in functions are limited to the scope of the function, and are deleted after the function ends. However, any existing variables that are changed are updated after the function is complete. Functions have the same requirements for names as variables. The functions can take several parameters, separated by commas. The vartype should be a class.

## Returns
Return statements can be declared with the `return` keyword, like this: `return 22;`. Most of the time, you'd use return statements in functions. They can also return none, which can be done as `return none;` or simply `return;`. For now, return statements will not work as direct inputs to other functions. For example, trying to run `out(return 'Hello, World!');` won't work.

## Imports
Imports are simple, but not yet fully functional. For now, imports are relative to the main file, but this is subject to change, so avoid importing files from other directories in imported files from other directories for now. To import a file, do `import {FILEPATH RELATIVE TO MAIN FILE}`. Imports simply put all the code of the import into the main code, so they are for organisational purposes only. Import statements only work in the root layer. Imports are handled during packaging, not during runtime.

# Permissions
## Reasoning
Permissions are used as an easy indicator for end-users as to what a program does to their system. They are stored in plain text in the program files.

## Declaring Permissions
Permission declaration is an exception to the semicolon rule; however, permissions must be declared in the first line. Declared permissions are separated by commas. Spaces should not be put in between permissions. They are declared as follows: `PERMISSIONS {PERMISSIONS BEING DECLARED}`. Unlike the rest of the code, these are separated from the rest of the code when the software is encoded, which is why they do not require, and in fact should not have, a semicolon at the end. It is unadvisable to declare more permissions than those that are used, as they could be suspicious for the end user, and permissions can also be added later. Some permissions also restrict the execution to the superuser (root).

## Additional Information
Permissions that make the program unrunnable by users other than root begin with `sudo.` in their name.

## Permissions That Exist
### sudo.runAsIs
Restrictions: Can only be run as root, key with which program is signed must be listed in /cfg/canRunAsIs\
This permission is used to run code as python instead of ROSC. It is very dangerous as it can escape the simulated environment. Excersise extreme caution when executing any programs that have this permission.

### directoryInformation
Restrictions: none\
This permission is required to view directory information, and is required in order to execute the getActiveDirectory() function.

### writeToFile
Restrictions: none\
This permission is required for the writeToFile() function

### readFromFile
Restrictions: none\
This permission is required for the readFromFile() function and getAudioSegmentFromWavFile() function

### readCurrentTime
Restrictions: none\
This permission is required for the getCurrentTimestamp() function

# Literal Expressions
## Lists
Lists are declared by wrapping the entries, separated by commas, in square brackets.

## Strings
Strings are declared by enclosing the text in either double quotes or single quotes. In a string, a backslash (\\), can be used to write symbols that would otherwise have a different meaning literally. For example, the string literal `"\""` would result in a string with the value being a double quote (`"`).

## Booleans
These literal expressions are declared with the keywords `true` and `false` for true and false respectively.

## Numbers
These literal expressions are declared by simply using valid numbers, with or without a decimal. Decimals should be denoted with a dot (.), because commas are used as separators in many things in ROSC.

## None
The literal `none` returns none.