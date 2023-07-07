from config import *
import os
import sys
from sys import exit

BLANK_PRE = "  "
NAME_TYPE_STR_COUNT = 25
NAME_STR_COUNT = 10

class Flag(object):
    def __init__(self, name, type=None, little_name=None, default_value=None, detail=None):
        self.name = name
        self.type = type
        self.little_name = little_name
        self.default_value = default_value
        self.detail = detail
        self.value = default_value

        if type is None:
            self.is_bool = True
        else:
            self.is_bool = False
    
    def get_type_str(self, type_):
        type_str = str(type_)[8:-2]
        if type_str == "str":
            return "string"
        else:
            return type_str


    def get_flag_str(self):
        flag_str = BLANK_PRE
        
        if self.little_name is not None:
            flag_str += f"-{self.little_name}, "
        else:
            flag_str += f"    "
        
        if self.type is not None:
            flag_str += "--" + (self.name + " " + self.get_type_str(self.type)).ljust(NAME_TYPE_STR_COUNT, " ")
        else:
            flag_str += "--" + (self.name.ljust(NAME_TYPE_STR_COUNT, " "))

        if self.detail is not None:
            flag_str += self.detail
        flag_str += "\n"
        return flag_str
    
    def change_value(self, value):
        if self.is_bool:
            self.value = value
        else:
            self.value = self.type(value)
            
        
    def get_value(self):
        return self.value

class Command(object):
    def __init__(self, name, detail):
        self.name = name
        self.detail = detail
        self.mandatory = []
        self.optional = []
        self.mandatory_count = 0
    
    def add_mandatory(self, name, type=None, little_name=None, default_value=None, detail=None):
        for flag in self.mandatory:
            if name == flag.name:
                raise Exception(f"{name} already exists")
            if little_name is not None and little_name == flag.little_name:
                raise Exception(f"{little_name} already exists")
        self.mandatory.append(Flag(name, type, little_name, default_value, detail))
        self.mandatory_count += 1
    
    def add_optional(self, name, type=None, little_name=None, default_value=None, detail=None):
        for flag in self.optional:
            if name == flag.name:
                raise Exception(f"{name} already exists")
            if little_name is not None and little_name == flag.little_name:
                raise Exception(f"{little_name} already exists")
        self.optional.append(Flag(name, type, little_name, default_value, detail))
    
    def get_command_str(self):
        command_str = ""
        command_str += f"{self.detail}\n\n"
        command_str += f"Usage:\n"
        command_str += f"{BLANK_PRE}{TD_NAME} {self.name}"
        for mandatory in self.mandatory:
            command_str += f" <{mandatory.name}>"
        command_str += " [flags]\n\n"
        command_str += f"Flags:\n"
        for optional in self.optional:
            optional_str = optional.get_flag_str()
            command_str += optional_str
        return command_str
    
    def print(self):
        print(self.get_command_str(), end="")
        exit()
    
    def help(self, arg):
        if arg == "--help" or arg == "-h":
            self.print()
    
    def mandatory_change_value(self, index, value):
        if index >= self.mandatory_count:
            self.print()
        try:
            self.mandatory[index].change_value(value)
        except:
            self.print()
    
    def get_optional_index(self, optional_name):
        for index, option in enumerate(self.optional):
            if optional_name == "--" + option.name or (option.little_name is not None and optional_name == "-" + option.little_name ):
                return index
        return None
    
    def optional_change_value(self, index, value):
        try:
            self.optional[index].change_value(value)
        except:
            self.print()

    def init_args(self, args):
        if len(args) < self.mandatory_count:
            self.print()
        i = 0
        mandatory_index = 0
        while i < len(args):
            arg = args[i]
            self.help(arg)
            optional_index = self.get_optional_index(arg)
            if optional_index is not None:
                if self.optional[optional_index].is_bool:
                    self.optional_change_value(optional_index, True)
                else:
                    try:
                        optional_value = args[i+1]
                    except:
                        self.print()
                    self.help(optional_value)
                    
                    self.optional_change_value(optional_index, optional_value)
                    
                    i += 1
            else:
                self.mandatory_change_value(mandatory_index, arg)
                mandatory_index += 1
            i += 1
    
    def get_args(self):
        args = {}
        for mandatory in self.mandatory:
            args[mandatory.name] = mandatory.value
        for optional in self.optional:
            args[optional.name] = optional.value
        return args

class Td(object):
    def __init__(self, detail):
        self.detail = detail
        self.command = []
        self.optional = []
        self.command_index = None
    
    def add_command(self, command):
        self.command.append(command)
    
    def add_optional(self, name, type=None, little_name=None, default_value=None, detail=None):
        for flag in self.optional:
            if name == flag.name:
                raise Exception(f"{name} already exists")
            if little_name is not None and little_name == flag.little_name:
                raise Exception(f"{little_name} already exists")
        self.optional.append(Flag(name, type, little_name, default_value, detail))
    
    def get_td_str(self):
        td_str = ""
        td_str += f"{self.detail}\n\n"
        td_str += f"Usage:\n"
        td_str += f"{BLANK_PRE}{TD_NAME} [command]\n\n"
        td_str += f"Available Commands:\n"
        for command in self.command:
            command_name_str = (command.name).ljust(NAME_STR_COUNT, " ")
            td_str += f"{BLANK_PRE}{command_name_str}{command.detail}\n"
        td_str += "\nFlags:\n"
        for optional in self.optional:
            optional_str = optional.get_flag_str()
            td_str += optional_str
        td_str += "\n"
        td_str += f"Use \"{TD_NAME} [command] --help\" for more information about a command.\n"

        return td_str
    
    def print(self):
        print(self.get_td_str(), end="")
        exit()
    
    def help(self, arg):
        if arg == "--help" or arg == "-h":
            self.print()
    
    def get_command_index(self, command_name):
        for index, command in enumerate(self.command):
            if command_name == command.name:
                return index
        self.print()
    
    def init_args(self):
        arg_count = len(sys.argv)

        if arg_count == 1:
            self.print()
        
        command_name = sys.argv[1]

        self.help(command_name)
        
        command_index = self.get_command_index(command_name)
        self.command_index = command_index

        self.command[command_index].init_args(sys.argv[2:])
    
    def get_args(self):
        if self.command_index is None:
            raise Exception(f"parameter not initialized")
        return self.command[self.command_index].get_args()