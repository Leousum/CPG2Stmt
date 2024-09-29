import copy

# 赋值语句
class Assign():
    def __init__(self) -> None:
        self.node_type = "Assignment"
        self.cpg_id = None
        self.code = None
        self.LValues = list() # 注意:赋值语句的左值可能有多个 e.g. String new_name = name1 = name = "test";
        self.RValue = None
    
    def to_string(self, level = -1):
        level += 1
        prefix = ""
        for i in range(level):
            prefix = "    " + prefix
        content = ""
        content += "\n" + (f"{prefix}----------------------------------------------")
        content += "\n" + (f"{prefix}| node_type: {self.node_type}")
        content += "\n" + (f"{prefix}| cpg_id: {self.cpg_id}")
        content += "\n" + (f"{prefix}| code: {self.code}")
        content += "\n" + (f"{prefix}| LValues: ")
        for i in range(len(self.LValues)):
            LValue = self.LValues[i]
            content += "\n" + (f"{prefix}    | LValues[{str(i)}]:")
            content += LValue.to_string(level + 1)
        content += "\n" + (f"{prefix}| RValue: ")
        if self.RValue is not None:
            content += self.RValue.to_string(level)
        content += "\n" + (f"{prefix}----------------------------------------------")
        return content
    
    def to_json(self):
        data = copy.deepcopy(self.__dict__)
        for i in range(len(self.LValues)):
            LValue = self.LValues[i]
            if LValue is not None:
                data['LValues'][i] = LValue.to_json()
        if self.RValue is not None:
            data['RValue'] = self.RValue.to_json()
        if "cpg_id" in data.keys():
            del data["cpg_id"]
        return data

# 类函数调用
class ObjCall():
    def __init__(self) -> None:
        self.node_type = "ObjCall"
        self.cpg_id = None
        self.code = None
        self.fullName = None
        self.obj = None
        self.method = None
        self.arguments = dict() # 实参字典 key为argument_index,value为argument
    
    def to_string(self, level = -1):
        level += 1
        prefix = ""
        for i in range(level):
            prefix = "    " + prefix
        content = ""
        content += "\n" + (f"{prefix}----------------------------------------------")
        content += "\n" + (f"{prefix}| node_type: {self.node_type}")
        content += "\n" + (f"{prefix}| cpg_id: {self.cpg_id}")
        content += "\n" + (f"{prefix}| code: {self.code}")
        content += "\n" + (f"{prefix}| fullName: {self.fullName}")
        content += "\n" + (f"{prefix}| obj: ")
        if self.obj is not None:
            content += self.obj.to_string(level + 1)
        content += "\n" + (f"{prefix}| method: ")
        if self.method is not None:
            content += self.method.to_string(level + 1)
        content += "\n" + (f"{prefix}| arguments: ")
        for argument_index in self.arguments.keys():
            argument = self.arguments[argument_index]
            content += "\n" + (f"{prefix}    | arguments[{argument_index}]:")
            content += argument.to_string(level + 1)
        content += "\n" + (f"{prefix}----------------------------------------------")
        return content
    
    def to_json(self):
        data = copy.deepcopy(self.__dict__)
        if self.obj is not None:
            data['obj'] = self.obj.to_json()
        if self.method is not None:
            data['method'] = self.method.to_json()
        data['arguments'] = dict()
        for argument_index in self.arguments.keys():
            argument = self.arguments[argument_index]
            if argument is not None:
                data['arguments'][argument_index] = argument.to_json()
        if "cpg_id" in data.keys():
            del data["cpg_id"]
        return data

# 普通函数调用
class CommonCall():
    def __init__(self) -> None:
        self.node_type = "CommonCall"
        self.cpg_id = None
        self.code = None
        self.fullName = None
        self.method = None
        self.arguments = dict() # 实参字典 key为argument_index,value为argument
    
    def to_string(self, level = -1):
        level += 1
        prefix = ""
        for i in range(level):
            prefix = "    " + prefix
        content = ""
        content += "\n" + (f"{prefix}----------------------------------------------")
        content += "\n" + (f"{prefix}| node_type: {self.node_type}")
        content += "\n" + (f"{prefix}| cpg_id: {self.cpg_id}")
        content += "\n" + (f"{prefix}| code: {self.code}")
        content += "\n" + (f"{prefix}| fullName: {self.fullName}")
        content += "\n" + (f"{prefix}| method: ")
        if self.method is not None:
            content += self.method.to_string(level + 1)
        content += "\n" + (f"{prefix}| arguments: ")
        for argument_index in self.arguments.keys():
            argument = self.arguments[argument_index]
            content += "\n" + (f"{prefix}    | arguments[{argument_index}]:")
            content += argument.to_string(level + 1)
        content += "\n" + (f"{prefix}----------------------------------------------")
        return content
    
    def to_json(self):
        data = copy.deepcopy(self.__dict__)
        if self.method is not None:
            data['method'] = self.method.to_json()
        for argument_index in self.arguments.keys():
            argument = self.arguments[argument_index]
            if argument is not None:
                data['arguments'][argument_index] = argument.to_json()
        if "cpg_id" in data.keys():
            del data["cpg_id"]
        return data

# 函数定义
class Method():
    def __init__(self) -> None:
        self.node_type = None # ObjMethod,CommonMethod
        self.obj_class_type = None # 所属类名称
        self.fullName = None # 即methodFullName e.g. :<module>.student.find_min
        self.shotName = None # e.g. find_min
        self.parameters = dict() # 形参字典
        self.parameter_types = list() # 形参类型列表
        self.methodReturn = None # 函数返回值的属性
        self.signature = None # <类:返回值类型 函数名称(参数类型1, 参数类型2, ...)>
        self.update_signature()
    
    def update_signature(self):
        self.signature = "<"
        if self.obj_class_type:
            self.signature += self.obj_class_type + ": "
        if self.methodReturn:
            self.signature += self.methodReturn + " "
        if self.shotName:
            self.signature += self.shotName + "("
        if self.parameter_types:
            for i in range(len(self.parameter_types)):
                parameter_type = self.parameter_types[i]
                self.signature += parameter_type
                if i != (len(self.parameter_types) - 1):
                    self.signature += ","
                else:
                    self.signature += ")>"
        else:
            self.signature += ")>"
    
    def to_string(self, level = -1):
        level += 1
        prefix = ""
        for i in range(level):
            prefix = "    " + prefix
        content = ""
        content += "\n" + (f"{prefix}----------------------------------------------")
        content += "\n" + (f"{prefix}| node_type: {self.node_type}")
        content += "\n" + (f"{prefix}| obj_class_type: {self.obj_class_type}")
        content += "\n" + (f"{prefix}| fullName: {self.fullName}")
        content += "\n" + (f"{prefix}| shotName: {self.shotName}")
        content += "\n" + (f"{prefix}| parameters: {str(self.parameters)}")
        content += "\n" + (f"{prefix}| parameter_types: {str(self.parameter_types)}")
        content += "\n" + (f"{prefix}| methodReturn: {self.methodReturn}")
        content += "\n" + (f"{prefix}| signature: {self.signature}")
        content += "\n" + (f"{prefix}----------------------------------------------")
        return content
    
    def to_json(self):
        data = copy.deepcopy(self.__dict__)
        for parameter_index in self.parameters.keys():
            parameter = self.parameters[parameter_index]
            if parameter is not None:
                data['parameters'][parameter_index] = parameter.to_json()
        if "cpg_id" in data.keys():
            del data["cpg_id"]
        return data
    
# 函数返回
class MethodReturn():
    def __init__(self) -> None:
        self.node_type = "MethodReturn"
        self.cpg_id = None
        self.code = None
        self.return_result = None
    
    def to_string(self, level = -1):
        level += 1
        prefix = ""
        for i in range(level):
            prefix = "    " + prefix
        content = ""
        content += "\n" + (f"{prefix}----------------------------------------------")
        content += "\n" + (f"{prefix}| node_type: {self.node_type}")
        content += "\n" + (f"{prefix}| cpg_id: {self.cpg_id}")
        content += "\n" + (f"{prefix}| code: {self.code}")
        content += "\n" + (f"{prefix}| return_result: ")
        if self.return_result is not None:
            content += self.return_result.to_string(level)
        content += "\n" + (f"{prefix}----------------------------------------------")
        return content
    
    def to_json(self):
        data = copy.deepcopy(self.__dict__)
        if self.return_result is not None:
            data['return_result'] = self.return_result.to_json()
        if "cpg_id" in data.keys():
            del data["cpg_id"]
        return data

if __name__ == "__main__":
    test = Method()
    test.node_type = "CommonMethod"
    test.obj_class_type = None
    test.fullName = "include_once"
    test.shotName = "include_once"
    test.parameters = dict() # 形参字典
    test.parameter_types = ["ANY"]
    test.methodReturn = "ANY"
    test.update_signature()
    print(test.signature)
    print(test.to_json())