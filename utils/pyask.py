'''
author: Justin Garza

description:
used to ask questions and get user's response

#TODO 🔳 create unit-tests
#TODO 🔳 run the unit-tests

'''



import re
import os



def assertIsInstance(var, datatype,message):
    if isinstance(var,datatype) == False:
        raise ValueError(message)

def ask(label, datatype):
    '''
    '''

    label = str(label)

    assertIsInstance(datatype,type,'datatype should be a type (i.e. str, int, float, etc)')

    done = False
    while done == False:
        try:
            if datatype != list:
                # i = datatype(input('what is the '+ label + '?:'))
                i = datatype(input(label))
                return i
            else:
                i = input('list the ' + label + '? (comma separated):')
                i = i.split(',')
                if len(i) == 0:
                    return []
                else:
                    return i
        except KeyboardInterrupt:
            print('cancelled by user')
            return None
        except:
            print('it should be a ' + datatype.__name__ + ', try again')

def ask_question(text, datatype):
    '''
    '''

    text = str(text)
    assertIsInstance(datatype,type,'datatype should be a type (i.e. str, int, float, etc)')

    done = False
    while done == False:
        try:
            i = datatype(input(text))
            return i
        except KeyboardInterrupt:
            print('cancelled by user')
            return None
        except:
            print('it should be a ' + datatype.__name__ + ', try again')

def ask_for_letter(text,exclude_list):
    '''
    '''
    letters = [
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 
    'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 
    'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 
    'Y', 'Z']

    text = str(text)
    assertIsInstance(str,type,'datatype should be a type (i.e. str, int, float, etc)')

    done = False
    while done == False:
        try:
            i = str(input(text)).upper()
            if len(i) == 1:
                if i not in exclude_list:
                    return i
                else:
                    print('you have already guessed that letter')
                    print('used letters: ',','.join(exclude_list))
            else:
                print('it should only be one letter')

        except:
            print('it should be 1 letter (A-Z), try again')

def _process(label,item):
    '''
    '''

    label = str(label)
    item = str(item)

    ask_types = {
        '{str}': str,
        '{int}': int,
        '{float}': float,
        '{list}': list,
    }

    try: 
        if re.match(r'{.+}',item):
            return ask(label,ask_types[item])
        else:
            return item
    except:
        return item

def process_dict(data, verbose =  False):

    assertIsInstance(data,dict,'data should be a dict')

    for d in data:
        if verbose:
            print(type(data[d]).__name__,d,data[d])
        if type(data[d]) == str:
            data[d] = _process(d,data[d])
        if type(data[d]) == dict:
            data[d] = process(data[d])
        if type(data[d]) == list:
            data[d] = process_list(data[d])
    return data

def process_list(template, verbose=False):
    '''
    '''

    assertIsInstance(template,list,'template should be a list')

    for i, item in enumerate(template):
        if verbose:
            print(i,type(item),item)
        if type(item) == str:
            template[i] = _process('index ' + str(i),item)
        if type(item) == dict:
            template[i] = process_dict(item, verbose=verbose)
        if type(item) == list:
            template[i] = process_list(item, verbose=verbose)
    return template

def process(data, verbose= False):
    if type(data) == dict:
        if verbose:
            print('this is a dict')
        data = process_dict(data, verbose=verbose)
    elif type(data) == list:
        if verbose:
            print('this is a list')
        data = process_list(data, verbose= verbose)
    return data

def ask_key_value():
    '''
    '''

    result = []

    done = False
    while done == False:
        i = ask_question('do you need to add a/another key-value pair?:\nN=no|Y=Yes\n',str)
        if i.upper() == 'Y':
            print('key = name of the key')
            print('value = value of the key')
            result.append({'key':'{str}','value':'{str}'})
            result = process_list(result)
        elif i.upper() == 'N':
            done = True
    return result

def ask_file(text='whats the file?:',file_type='.txt',hint='OOPS! something doesn\'t seem right, try again'):
    '''
    '''

    assertIsInstance(text,str,'text should be a str')
    assertIsInstance(file_type,str,'file_type should be a str')
    assertIsInstance(hint,str,'hint should be a str')

    text += '\n*drag and drop the {ft}\n*enter \\path\\to\\file{ft}\n'.format(ft=file_type)

    done = False
    while done == False:
        i = input(text)
        if os.path.exists(i) and i.endswith(file_type):
            return i 
            done = True
        else:
            print(hint)
            done = False

def ask_folder(text='what folder?:',hint='OOPS!, this should be a folder, try again'):
    text += '\n*drag and drop the folder\n*enter \\path\\to\\folder\\foldername\n'

    done = False
    while done == False:
        i = input(text)
        if os.path.exists(i):
            return i 
            done = True
        else:
            print(hint)
            done = False 

def choose_one(choices,text='choose one:',verbose=False):
    '''
    '''

    assertIsInstance(choices,list,'choices should be a list')
    assertIsInstance(text,str,'text should be a str')

    print(text)

    for i, item in enumerate(choices):
        print('\t',i,item)
    
    done = False
    while done == False:
        response = ask_question('',int)
        
        if response == None:
            # print('cancelled by user')
            return None
        
        if response >= 0 and response < len(choices):
            done = True
            return choices[response]
        else:
            if verbose:
                print('input a value from the choices')
            done = False

    

if __name__ == '__main__':
    pass

    data = {"name": "{str}","age": "{int}"}
    data = process_dict(data, verbose=True)
    print(data)

    data = [{"name": "{str}","age": "{int}"},"{str}","{int}"]
    data = process_list(data, verbose=True)
    print(data)
