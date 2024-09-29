import copy

# 控制结构
class ControlStructure():
    def __init__(self) -> None:
        self.node_type = "ControlStructure"
        self.cpg_id = None
        self.code = None
        self.controlStructureType = None # e.g. "IF","ELSE","WHILE","SWITCH","BREAK"
        self.condition = None
    
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
        content += "\n" + (f"{prefix}| controlStructureType: {self.controlStructureType}")
        if self.condition is not None:
            content += self.condition.to_string(level)
        content += "\n" + (f"{prefix}----------------------------------------------")
        return content
    
    def to_json(self):
        data = copy.deepcopy(self.__dict__)
        if "cpg_id" in data.keys():
            del data["cpg_id"]
        return data