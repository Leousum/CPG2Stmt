import copy

# 对象
class Obj():
    def __init__(self, cpg_id = None, code = None, class_type = None, identifier = None) -> None:
        self.node_type = "Object"
        self.cpg_id = cpg_id
        self.code = code
        self.class_type = class_type # e.g. "Student","Teacher"
        self.identifier = identifier # e.g. "student","teacher"
        self.signature = f"<[{self.node_type}]: {self.class_type}: {self.identifier}>"
    
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
        content += "\n" + (f"{prefix}| class_type: {self.class_type}")
        content += "\n" + (f"{prefix}| identifier: {self.identifier}")
        content += "\n" + (f"{prefix}| signature: {self.signature}")
        content += "\n" + (f"{prefix}----------------------------------------------")
        return content
    
    def to_json(self):
        data = copy.deepcopy(self.__dict__)
        if "cpg_id" in data.keys():
            del data["cpg_id"]
        return data

# 变量
class Variable():
    def __init__(self, cpg_id = None, code = None, type = None, identifier = None) -> None:
        self.node_type = "Variable"
        self.cpg_id = cpg_id
        self.code = code
        self.type = type # e.g. "java.util.String"
        self.identifier = identifier # e.g. "name"
        self.value = None # e.g. "leousum"
        self.signature = f"<[{self.node_type}]: {self.type}: {self.identifier}>"
    
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
        content += "\n" + (f"{prefix}| type: {self.type}")
        content += "\n" + (f"{prefix}| identifier: {self.identifier}")
        content += "\n" + (f"{prefix}| value: {self.value}")
        content += "\n" + (f"{prefix}| signature: {self.signature}")
        content += "\n" + (f"{prefix}----------------------------------------------")
        return content
    
    def to_json(self):
        data = copy.deepcopy(self.__dict__)
        if "cpg_id" in data.keys():
            del data["cpg_id"]
        return data

# 对象属性
class ObjField():
    def __init__(self) -> None:
        self.node_type = "Object_Field"
        self.cpg_id = None
        self.obj = None
        self.code = None # e.g. s1.name
        self.type = None # e.g. "java.util.String"
        self.identifier = None # e.g. "name"
        self.value = None # e.g. "leousum"
        self.signature = None
        self.update_signature()
    
    def update_signature(self):
        if self.obj is not None:
            self.signature = f"<[{self.node_type}]: {self.obj.class_type}: {self.obj.identifier}: {self.type}: {self.identifier}>"
        else:
            self.signature = f"<[{self.node_type}]: {self.type}: {self.identifier}>"
    
    def to_string(self, level = -1):
        level += 1
        prefix = ""
        for i in range(level):
            prefix = "    " + prefix
        content = ""
        content += "\n" + (f"{prefix}----------------------------------------------")
        content += "\n" + (f"{prefix}| node_type: {self.node_type}")
        content += "\n" + (f"{prefix}| cpg_id: {self.cpg_id}")
        content += "\n" + (f"{prefix}| obj:")
        if self.obj is not None:
            content += self.obj.to_string(level)
        content += "\n" + (f"{prefix}| code: {self.code}")
        content += "\n" + (f"{prefix}| type: {self.type}")
        content += "\n" + (f"{prefix}| identifier: {self.identifier}")
        content += "\n" + (f"{prefix}| value: {self.value}")
        content += "\n" + (f"{prefix}| signature: {self.signature}")
        content += "\n" + (f"{prefix}----------------------------------------------")
        return content
    
    def to_json(self):
        data = copy.deepcopy(self.__dict__)
        if self.obj is not None:
            data['obj'] = self.obj.to_json()
        if "cpg_id" in data.keys():
            del data["cpg_id"]
        return data

# 字面量
class Literal():
    def __init__(self, type = None, value = None) -> None:
        self.node_type = "Literal"
        self.type = type # e.g. "java.lang.String"
        self.value = value # e.g. "leousum"
        self.code = value
        # TODO:如何根据type将value转为相应的类型呢?
    
    def to_string(self, level = -1):
        level += 1
        prefix = ""
        for i in range(level):
            prefix = "    " + prefix
        content = ""
        content += "\n" + (f"{prefix}----------------------------------------------")
        content += "\n" + (f"{prefix}| node_type: {self.node_type}")
        content += "\n" + (f"{prefix}| type: {self.type}")
        content += "\n" + (f"{prefix}| value: {self.value}")
        content += "\n" + (f"{prefix}----------------------------------------------")
        return content
    
    def to_json(self):
        return copy.deepcopy(self.__dict__)

# 数据操作
class Operation():
    def __init__(self) -> None:
        self.node_type = "Operation"
        self.cpg_id = None
        self.code = str()
        self.operator = None # 操作符号,e.g. "<operator>.addition"
        self.operands = list() # 操作数列表
        self.type = None
        self.value = None

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
        content += "\n" + (f"{prefix}| operator: {self.operator}")
        content += "\n" + (f"{prefix}| operands: ")
        for i in range(len(self.operands)):
            operand = self.operands[i]
            content += "\n" + (f"{prefix}    | operands[{str(i)}]:")
            content += operand.to_string(level + 1)
        content += "\n" + (f"{prefix}----------------------------------------------")
        return content
    
    def to_json(self):
        data = copy.deepcopy(self.__dict__)
        for i in range(len(self.operands)):
            operand = self.operands[i]
            if operand is not None:
                data['operands'][i] = operand.to_json()
        if "cpg_id" in data.keys():
            del data["cpg_id"]
        return data

# 临时变量(可以代表任何类型的变量)
class Temporary():
    def __init__(self) -> None:
        self.node_type = "Temporary"
        self.type = None
        self.identifier = None
        self.value = None
        self.is_class = False
    
    def to_string(self, level = -1):
        level += 1
        prefix = ""
        for i in range(level):
            prefix = "    " + prefix
        content = ""
        content += "\n" + (f"{prefix}----------------------------------------------")
        content += "\n" + (f"{prefix}| node_type: {self.node_type}")
        content += "\n" + (f"{prefix}| type: {self.type}")
        content += "\n" + (f"{prefix}| identifier: {self.identifier}")
        content += "\n" + (f"{prefix}| value: {self.value}")
        content += "\n" + (f"{prefix}| is_class: {self.is_class}")
        content += "\n" + (f"{prefix}----------------------------------------------")
        return content
    
    def to_json(self):
        return copy.deepcopy(self.__dict__)

if __name__ == "__main__":
    s1 = Obj(111, "s1", "Student", "s1")
    test = ObjField()
    test.cpg_id = 222
    test.obj = s1
    test.code = "s1.name"
    test.type = "java.util.String"
    test.identifier = "name"
    test.value = "leousum"
    test.signature = None
    test.update_signature()
    print(test.to_string())
    print(test.to_json())