import os
import copy
import json
import time
import shutil
import subprocess

from utils.log_manager import LogManager
from stmt.control_structure import ControlStructure
from stmt.stmt_data import Obj, ObjField, Variable, Literal, Operation, Temporary
from stmt.stmts import Assign, CommonCall, ObjCall, Method, MethodReturn
from cpgql.client import CPGQLSClient
from cpgql.queries import import_code_query, import_cpg_query, close_query, exit_joern

class JoernServer():
    def __init__(self, config_file, repo_path, log_manager, checkout_tag = None):
        # You can start local joern service manually with the command "joern --server --server-host localhost --server-port 8989"
        self.log_level = 0
        self.config_file = config_file
        self.repo_path = repo_path
        self.log_manager = log_manager
        self.log_manager.log_info(f'Start Static Analysis', True, 0)
        self.start_joern_service(config_file["joern_server_point"])
        self.joern_client = CPGQLSClient(config_file["joern_server_point"])
        self.project_name = os.path.basename(repo_path)
        if checkout_tag is not None:
            self.project_name = self.project_name + "_" + str(checkout_tag)
        workspcae_path =  os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")), "workspace")
        self.cpg_path = os.path.join(workspcae_path, self.project_name, "cpg.bin")
        self.log_manager.log_info(f'Construct CPG...', False, 1)
        if os.path.exists(self.cpg_path):
            self.log_manager.log_info(f'Project with name `{self.project_name}` already exists', False, 1)
            self.joern_client.execute(import_cpg_query(self.cpg_path))
        else:
            self.log_manager.log_info(f'Creating project `{self.project_name}` for code at `{repo_path}`', False, 1)
            self.joern_client.execute(import_code_query(repo_path, self.project_name))
        self.log_manager.log_info(f'Construct CPG Success!', False, 1)
        self.type_map_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")), "cpgql", "type_map.json")
        self.query_result_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")), "query")
        if not os.path.exists(self.query_result_path):
            os.makedirs(self.query_result_path, mode = 0o777)
        self.type_map = dict()
        with open(self.type_map_path, "r", encoding = "utf-8") as f:
            self.type_map = json.load(f)
        self.variable_types = list(self.type_map.keys()) # 变量类型列表
        self.MAX_QUERY_COUNT = 2200
        self.query_count = 0

    def start_joern_service(self, server_point):
        try:
            # Run command in background without displaying any output
            port = server_point[server_point.find(":") + 1:]
            command = ["joern", "--server", "--server-host", "localhost", "--server-port", port]
            subprocess.Popen(command, stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL, start_new_session = True)
            # Wait until the Joern service start to prevent subsequent processes from being affected
            time.sleep(10)
            self.log_manager.log_info(f"Joern Service Start Successfully!", False, self.log_level)
        except:
            self.log_manager.log_info(f"Joern Service Start Failed!", False, self.log_level)
    
    def restart_joern_service(self):
        try:
            self.close_cpg()
            self.query_count = 0
            server_point = self.config_file["joern_server_point"]
            # port = server_point[server_point.find(":") + 1:]
            # os.system(f"fuser -k {port}/tcp") # TODO: 判断是否需要此命令
            self.start_joern_service(server_point)
            self.joern_client = CPGQLSClient(server_point)
            self.log_manager.log_info(f'Restarting CPG...', False, 1)
            if os.path.exists(self.cpg_path):
                self.joern_client.execute(import_cpg_query(self.cpg_path))
            else:
                self.joern_client.execute(import_code_query(self.repo_path, self.project_name))
            self.log_manager.log_cost("restart_count", 1)
        except Exception as e:
            self.log_manager.log_info(f"Joern Service Restart Failed!", False, self.log_level)
            raise(e)

    def close_cpg(self):
        try:
            if os.path.exists(self.query_result_path):
                shutil.rmtree(self.query_result_path)
            self.joern_client.execute(close_query(self.project_name))
            self.joern_client.execute(exit_joern())
        except:
            pass
        self.log_manager.log_info(f"Joern Service Shut Down Successfully!", False, self.log_level)
    
# ======================================== Convert json to stmt Start ========================================
    def json2stmt(self, data: dict):
        # 将json格式的数据转换为Stmt类型
        stmt = None
        if data is not None and isinstance(data, dict) and "node_type" in data.keys():
            if data["node_type"] == "Assignment":
                stmt = Assign()
                stmt.code = data["code"]
                for LValue in data["LValues"]:
                    stmt.LValues.append(self.json2stmt(LValue))
                stmt.RValue = self.json2stmt(data["RValue"])
            elif data["node_type"] == "ObjCall":
                stmt = ObjCall()
                stmt.code = data["code"]
                stmt.fullName = data["fullName"]
                stmt.obj = self.json2stmt(data["obj"])
                stmt.method = self.json2stmt(data["method"])
                for argument_index in data["arguments"].keys():
                    argument = data["arguments"][argument_index]
                    if argument is not None:
                        stmt.arguments[argument_index] = self.json2stmt(argument)
            elif data["node_type"] == "CommonCall":
                stmt = CommonCall()
                stmt.code = data["code"]
                stmt.fullName = data["fullName"]
                stmt.method = self.json2stmt(data["method"])
                for argument_index in data["arguments"].keys():
                    argument = data["arguments"][argument_index]
                    if argument is not None:
                        stmt.arguments[argument_index] = self.json2stmt(argument)
            elif data["node_type"] in ["ObjMethod", "CommonMethod"]:
                stmt = Method()
                stmt.obj_class_type = data["obj_class_type"]
                stmt.fullName = data["fullName"]
                stmt.shotName = data["shotName"]
                for parameter_index in data["parameters"].keys():
                    parameter = data["parameters"][parameter_index]
                    if parameter is not None:
                        stmt.parameters[parameter_index] = self.json2stmt(parameter)
                stmt.parameter_types = copy.deepcopy(data["parameter_types"])
                stmt.methodReturn = data["methodReturn"] # 注意Method()类的methodReturn属性是一个字符串
                stmt.signature = data["signature"]
                stmt.update_signature()
            elif data["node_type"] == "MethodReturn":
                stmt = MethodReturn()
                stmt.code = data["code"]
                stmt.return_result = self.json2stmt(data["return_result"])
            elif data["node_type"] == "Object":
                stmt = Obj(cpg_id = None, code = data["code"], class_type = data["class_type"], identifier = data["identifier"])
            elif data["node_type"] == "Variable":
                stmt = Variable(cpg_id = None, code = data["code"], type = data["type"], identifier = data["identifier"])
            elif data["node_type"] == "Object_Field":
                stmt = ObjField()
                stmt.obj = self.json2stmt(data["obj"])
                stmt.code = data["code"]
                stmt.type = data["type"]
                stmt.identifier = data["identifier"]
                stmt.value = data["value"]
                stmt.update_signature()
            elif data["node_type"] == "Literal":
                stmt = Literal()
                stmt.type = data["type"]
                stmt.value = data["value"]
                stmt.code = data["code"]
            elif data["node_type"] == "Operation":
                stmt = Operation()
                stmt.code = data["code"]
                stmt.operator = data["operator"]
                for operand in data["operands"]:
                    stmt.operands.append(self.json2stmt(operand))
                stmt.type = data["type"]
                stmt.value = data["value"]
            elif data["node_type"] == "Temporary":
                stmt = Temporary()
                stmt.type = data["type"]
                stmt.identifier = data["identifier"]
                stmt.value = data["value"]
                stmt.is_class = data["is_class"]
            elif data["node_type"] == "ControlStructure":
                stmt = ControlStructure()
                stmt.code = data["code"]
                stmt.controlStructureType = data["controlStructureType"]
                stmt.condition = self.json2stmt(data["condition"])
        return stmt
# ======================================== Convert json to stmt End ========================================

# ======================================== Convert String Start ========================================
    # Extract a list from a string
    def string2dictlist(self, text):
        result = list()
        if text.find("[") != -1 and text.find("]") != -1 and text.find("{") != -1 and text.find("}") != -1:
            text = text.strip("[]").replace("\\", "").replace('\"', "'").replace('"', "'")
            content_dicts = text.split("},{")
            for content_dict in content_dicts:
                content_dict = content_dict.strip("{}")
                content = dict()
                key_values = content_dict.split(",'")
                last_k = None
                for key_value in key_values:
                    if key_value.find(":") != -1:
                        k_v_list = key_value.split("':")
                        if len(k_v_list) >= 2:
                            k = key_value.split("':")[0].strip("'")
                            v = key_value.split("':")[1].strip("'")
                            if v.startswith("[") and v.endswith("]"):
                                v = v.strip("[]").split(",")
                                if v == ['']:
                                    v = []
                            if k in ["id", "order", "lineNumber", "argumentIndex"]:
                                v = int(v)
                            content[k] = v
                            last_k = k
                    else:
                        if last_k is not None:
                            if isinstance(content[last_k], str) and isinstance(key_value, str):
                                content[last_k] += key_value
                        if isinstance(content[last_k], str) and content[last_k].startswith("[") and content[last_k].endswith("]"):
                            try:
                                content[last_k] = json.loads(content[last_k])
                            except:
                                try:
                                    content[last_k] = content[last_k].strip("[]").split(",")
                                    if content[last_k] == ['']:
                                        content[last_k] = []
                                except:
                                    pass
                if content != {}:
                    result.append(content)
        else:
            text = text.strip("[]").replace("\\", "").replace('\"', "'").replace('"', "'")
            result = text.split(",")
            for i in range(0, len(result)):
                result[i] = result[i].strip("'").strip('"')
        return result

    # Extract a list from a string
    def str2list(self, text):
        text_list = list()
        try:
            if text.find("[") != -1 and text.rfind("]") != -1:
                text = text[text.find("["):text.rfind("]") + 1]
                try:
                    # 替换特殊字符
                    input_string = text
                    characters_to_remove = ["\r", "\n", "\t", "\b", "\f"]
                    for char in characters_to_remove:
                        input_string = input_string.replace(char, "")
                    # 删除旧文件
                    txt_file_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")), "temp.txt")
                    if os.path.exists(txt_file_path):
                        os.remove(txt_file_path)
                    json_file_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")), "temp.json")
                    if os.path.exists(json_file_path):
                        os.remove(json_file_path)
                    # 存入txt文件
                    with open(txt_file_path, "w", encoding = "utf-8") as txt_file:
                        txt_file.write(input_string)
                    # 更改文件后缀
                    os.rename(txt_file_path, json_file_path)
                    # 从json文件读取内容
                    if os.path.exists(json_file_path):
                        with open(json_file_path, 'r', encoding = "utf-8") as json_file:
                            result = json.load(json_file)
                            if isinstance(result, list):
                                return result
                except:
                    pass
                infos = text.split("\n")
                text = "".join(infos).strip()
                text_list = json.loads(text.replace("\\", ""))
        except:
            try:
                text_list = self.string2dictlist(text)
            except Exception as e:
                print(f"*{text}*")
                raise(e)
        return text_list
# ======================================== Convert String End ========================================

# ======================================== Base Function Start ========================================

    def find_nodes(self, cpg_type: str, conditions: list, restricts: list):
        '''
        Find nodes based on the condition
        '''
        query = "cpg." + cpg_type
        for condition in conditions:
            query += f'.filter(node => {condition})'
        for restrict in restricts:
            query += f'.{restrict}'
        query += ".toJson"
        nodes = list()
        is_queried = False
        query_file_path = os.path.join(self.query_result_path, query.replace(".", "_").replace(" ", "") + ".json")
        if os.path.exists(query_file_path):
            try:
                with open(query_file_path, "r", encoding = "utf-8") as f:
                    nodes = json.load(f)
                is_queried = True
            except:
                nodes = list()
        if not is_queried:
            try:
                # 2024年10月10日发现: Joern查询次数达到2600次以上时就会崩溃,我们需要自动重启Joern服务
                if self.query_count >= self.MAX_QUERY_COUNT:
                    self.restart_joern_service()
                query_result = None
                try:
                    query_result = self.joern_client.execute(query)["stdout"]
                except:
                    self.restart_joern_service()
                    query_result = self.joern_client.execute(query)["stdout"]
                query_result = query_result[query_result.find("=") + 1:].strip()
                self.query_count += 1
                nodes = self.str2list(query_result)
                self.log_manager.log_info(f"CPG Query Success: {query}", False, self.log_level)
                try:
                    with open(query_file_path, "w", encoding = "utf-8") as f:
                        json.dump(nodes, f, ensure_ascii = False, indent = 4)
                except:
                    pass
            except Exception as e:
                nodes = list()
                self.log_manager.log_info(f"CPG Query Fail: {query}", False, self.log_level)
                raise(e)
        return nodes
    
    def remove_duplicate_nodes(self, nodes: list):
        node_ids = list()
        new_nodes = list()
        for node in nodes:
            if isinstance(node, dict):
                if "id" in node.keys():
                    if node["id"] not in node_ids:
                        node_ids.append(node["id"])
                        new_nodes.append(node)
        return new_nodes
    
    def check_block(self, nodes: list):
        # 检查Nodes列表,处理其中的BLOCK节点
        result = list()
        if isinstance(nodes, list):
            for node in nodes:
                if isinstance(node, dict):
                    if "_label" in node.keys():
                        if node["_label"] == "BLOCK":
                            cfgIn_nodes = self.find_cfgIn(node)
                            if isinstance(cfgIn_nodes, list):
                                if len(cfgIn_nodes) > 0:
                                    result.append(cfgIn_nodes[0])
                        else:
                            result.append(node)
        return result

    def find_cpg_node_by_id(self, cpg_id):
        nodes = self.find_nodes(
            cpg_type = "all",
            conditions = [f"node.id=={str(cpg_id)}"],
            restricts = []
        )
        if nodes != []:
            return nodes[0]
        return None

    def find_cpg_call_node_location(self, cpg_node: dict):
        node_id = cpg_node["id"]
        nodes = self.find_nodes(
            cpg_type = "call",
            conditions = [f"node.id=={str(node_id)}"],
            restricts = ["map(x=>(x.node.location.filename, x.node.location.lineNumber))"]
        )
        if nodes != []:
            return nodes[0]
        return None
    
    def find_cpg_call_node_location_by_id(self, cpg_id):
        nodes = self.find_nodes(
            cpg_type = "call",
            conditions = [f"node.id=={str(cpg_id)}"],
            restricts = ["map(x=>(x.node.location.filename, x.node.location.lineNumber))"]
        )
        if nodes != []:
            return nodes[0]
        return None
    
    def find_path_line(self, node_or_id: any):
        cpg_id = None
        if isinstance(node_or_id, dict):
            if "id" in node_or_id.keys():
                cpg_id = node_or_id["id"]
        elif isinstance(node_or_id, str):
            cpg_id = node_or_id
        relative_path = None
        abs_path = None
        lineNum = None
        if cpg_id is not None:
            location_node = self.find_cpg_call_node_location_by_id(cpg_id)
            if location_node is not None:
                for k in location_node.keys():
                    if k is not None and k not in ["", "N/A"]:
                        relative_path = k
                        abs_path = os.path.join(self.repo_path, relative_path)
                        lineNum = int(location_node[k])
                        if os.path.exists(abs_path):
                            break
        return relative_path, abs_path, lineNum
    
    def find_dominate_nodes(self, cpg_type: str, cpg_node: dict):
        node_id = cpg_node["id"]
        dominate_nodes = self.find_nodes(
            cpg_type = cpg_type,
            conditions = [f'node.id=={str(node_id)}'],
            restricts = ["dominates", "sortBy(node => node.lineNumber)"] # "isCall"
        )
        return dominate_nodes

    def check_dominate_node(self, branch_node: dict, source_node: dict):
        # 通过dominates方法检查source_node是否处于branch_node所在分支
        branch_id = str(branch_node["id"])
        source_id = str(source_node["id"])
        if branch_id == source_id:
            return True
        nodes = self.find_nodes(
            cpg_type = "call",
            conditions = [f"node.id=={branch_id}"],
            restricts = ["dominates", "isCall", f"filter(node => node.id=={source_id})", "map(x=> (x.node.id, x.node.id))"]
        )
        for node in nodes:
            if isinstance(node, dict):
                if "_1" in node.keys():
                    if str(node["_1"]) == source_id:
                        return True
        return False

    def find_node_contain(self, parameter: str):
        conditions = list()
        if parameter is not None:
            conditions.append(f'node.code.contains("{parameter}")')
        nodes = self.find_nodes(
            cpg_type = "call",
            conditions = conditions,
            restricts = ["sortBy(node => node.lineNumber)"]
        )
        return nodes
    
# ======================================== Base Function End ========================================

# ======================================== AST Functions Start ========================================
    def find_astChildren(self, cpg_node: dict):
        node_id = cpg_node["id"]
        ast_children_nodes = self.find_nodes(
            cpg_type = "call",
            conditions = [f"node.id=={str(node_id)}"],
            restricts = ["astChildren"]
        )
        return ast_children_nodes

    def find_astParent(self, cpg_node: dict):
        node_id = cpg_node["id"]
        ast_parent_nodes = self.find_nodes(
            cpg_type = "call",
            conditions = [f"node.id=={str(node_id)}"],
            restricts = ["astParent"]
        )
        return ast_parent_nodes

    def find_astParent_until_top(self, cpg_node: dict):
        # 找到最上层的AST父节点(可能是CALL、CONTROL_STRUCTURE、RETURN三种类型)
        if cpg_node is None:
            return cpg_node
        if cpg_node["_label"] == "RETURN":
            return cpg_node
        else:
            ast_parent_nodes = self.find_astParent(cpg_node)
            if ast_parent_nodes == []:
                control_node = self.get_control_node(cpg_node)
                if control_node is not None:
                    return control_node
                else:
                    return cpg_node
            elif ast_parent_nodes[0]["_label"] == "BLOCK":
                return cpg_node
            else:
                if ast_parent_nodes[0] is not None:
                    return self.find_astParent_until_top(ast_parent_nodes[0])
                else:
                    return cpg_node
# ======================================== AST Functions End ========================================

# ======================================== CFG Functions Start ========================================
    def find_cfgIn(self, cpg_node: dict):
        node_id = cpg_node["id"]
        cfg_in_nodes = self.find_nodes(
            cpg_type = "all",
            conditions = [f"node.id=={str(node_id)}"],
            restricts = ["_cfgIn"]
        )
        return cfg_in_nodes
    
    def find_cfgIn_ids(self, node_id):
        cfg_in_ids = list()
        if node_id is not None:
            cfg_in_ids = self.find_nodes(
                cpg_type = "all",
                conditions = [f"node.id=={str(node_id)}"],
                restricts = ["_cfgIn", "map(x=> (x.node.id))"]
            )
        cfg_in_ids = list(set(cfg_in_ids))
        return cfg_in_ids
    
    def find_cfgOut(self, cpg_node: dict):
        node_id = cpg_node["id"]
        cfg_out_nodes = self.find_nodes(
            cpg_type = "all",
            conditions = [f"node.id=={str(node_id)}"],
            restricts = ["_cfgOut"]
        )
        return cfg_out_nodes
    
    def find_cfgNext_until_call(self, cpg_node: dict):
        node_id = cpg_node["id"]
        nodes = self.find_nodes(
            cpg_type = "call",
            conditions = [f"node.id=={str(node_id)}"],
            restricts = ["repeat(_.cfgNext)(_.until(_.isCall))"]
        )
        cfg_next_nodes = self.remove_duplicate_nodes(nodes)
        return cfg_next_nodes

    def find_cfgOut_until_call(self, cpg_node: dict, is_control_node: bool):
        # 注意:控制结构,例如IF,SWITCH语句也被视为调用语句
        # is_control_node为True时,表示该节点是控制结构,要找后续的调用节点
        nodes = list()
        cfg_out_nodes = self.find_cfgOut(cpg_node)
        # 当一个节点的CFG后继节点有多个时,这个节点有可能是一个控制结构节点
        if not is_control_node:
            if len(cfg_out_nodes) > 1:
                if self.is_control_structure(cpg_node):
                    return [cpg_node]
        for node in cfg_out_nodes:
            if node["_label"] != "CALL":
                if node["_label"] == "RETURN":
                    nodes.append(node)
                else:
                    nodes.extend(self.find_cfgOut_until_call(node, False))
            else:
                nodes.append(node)
        call_nodes = self.remove_duplicate_nodes(nodes)
        return call_nodes

    def find_cfg_successors(self, cpg_node: dict):
        # 找到CFG后继节点
        successors = list()
        if isinstance(cpg_node, dict):
            new_cpg_node = copy.deepcopy(cpg_node)
            is_control_node = False
            if cpg_node["_label"] == "CONTROL_STRUCTURE":
                is_control_node = True
                new_cpg_node = self.find_control_condition(cpg_node)
            nodes = list()
            if new_cpg_node is not None:
                cfg_out_call_nodes = self.find_cfgOut_until_call(new_cpg_node, is_control_node)
                for node in cfg_out_call_nodes:
                    nodes.append(self.find_astParent_until_top(node))
            successors = self.remove_duplicate_nodes(nodes)
            cpg_ids = list()
            for successor in successors:
                cpg_ids.append(str(successor["id"]))
            self.log_manager.log_info(f"Find [{cpg_node['id']} {cpg_node['code']}] {len(successors)} successors: [{','.join(cpg_ids)}]", False, self.log_level)
        return successors
# ======================================== CFG Functions End ========================================

# ======================================== Control Structure Functions Satrt ========================================
    def find_control_condition(self, cpg_node: dict):
        # 找到控制结构的条件
        node_id = cpg_node["id"]
        condition_nodes = self.find_nodes(
            cpg_type = "controlStructure",
            conditions = [f"node.id=={str(node_id)}"],
            restricts = ["condition"]
        )
        if condition_nodes:
            return condition_nodes[0]
        return None
    
    def find_controlledBy_nodes(self, cpg_node: dict):
        # 找到控制当前节点的节点
        if isinstance(cpg_node, dict) and "id" in cpg_node.keys():
            node_id = cpg_node["id"]
            controlledBy_nodes = self.find_nodes(
                cpg_type = "call",
                conditions = [f"node.id=={str(node_id)}"],
                restricts = ["controlledBy"]
            )
            if controlledBy_nodes is not None and isinstance(controlledBy_nodes, list):
                return controlledBy_nodes
        return []

    def is_control_structure(self, cpg_node: dict):
        # 判断一个节点是否是控制节点
        cfg_out_call_nodes = self.find_cfgOut_until_call(cpg_node, True)
        if cfg_out_call_nodes:
            cfg_out_call_node = cfg_out_call_nodes[0]
            controlledBy_nodes = self.find_controlledBy_nodes(cfg_out_call_node)
            if controlledBy_nodes:
                for controlledBy_node in controlledBy_nodes:
                    if isinstance(controlledBy_node, dict) and isinstance(cpg_node, dict):
                        if "id" in controlledBy_node.keys() and "id" in cpg_node.keys():
                            if controlledBy_node["id"] == cpg_node["id"]:
                                return True
        return False
    
    def get_lineNumber(self, cpg_node: dict):
        lineNumber = None
        if "lineNumber" in cpg_node.keys():
            lineNumber = int(str(cpg_node["lineNumber"]).replace("\\", "").replace("\"", "").replace("\'", ""))
        return lineNumber
    
    def get_control_node(self, cpg_node: dict):
        # 在不能根据astParent获得控制节点时使用此方法
        # 首先检查该节点是否是控制结构
        if cpg_node["_label"] == "CONTROL_STRUCTURE":
            return cpg_node
        # 方法一: 根据行号进行查找
        lineNumber = self.get_lineNumber(cpg_node)
        if lineNumber is not None:
            nodes1 = self.find_nodes(
                cpg_type = "controlStructure",
                conditions = [],
                restricts = [f"filter(_.lineNumber==Some(value = {str(lineNumber)}))"]
            )
            if nodes1:
                return nodes1[0]
        # 方法二: 根据代码
        code = cpg_node["code"]
        if code:
            nodes2 = self.find_nodes(
                cpg_type = "controlStructure",
                conditions = [],
                restricts = [f'filter(_.code.contains("{code}"))']
            )
            control_node = None
            if nodes2:
                # 查找node id相距最小的节点
                node_id = int(cpg_node["id"])
                min_distance = 1000
                for node in nodes2:
                    if isinstance(node, dict):
                        distance = abs(int(node["id"]) - node_id)
                        if distance <= min_distance:
                            control_node = node
                            min_distance = distance
                return control_node
        return None
    
    def find_for_parts(self, cpg_node: dict):
        # 查找for循环的初始化、条件和更新3个部分对应的CPG Nodes
        node_id = cpg_node["id"]
        target_nodes = self.find_nodes(
            cpg_type = "controlStructure",
            conditions = [f"node.id=={str(node_id)}"],
            restricts = ["astChildren", "isCall"]
        )
        return target_nodes
    
# ======================================== Control Structure Functions End ========================================

# ======================================== Assignment Functions Satrt ========================================
    def find_assign_targets(self, cpg_node: dict):
        node_id = cpg_node["id"]
        nodes = self.find_nodes(
            cpg_type = "call",
            conditions = [f"node.id=={str(node_id)}"],
            restricts = ["assignment", "target"]
        )
        target_nodes = self.check_block(nodes)
        return target_nodes

    def find_assign_sources(self, cpg_node: dict):
        node_id = cpg_node["id"]
        nodes = self.find_nodes(
            cpg_type = "call",
            conditions = [f"node.id=={str(node_id)}"],
            restricts = ["assignment", "source"]
        )
        source_nodes = self.check_block(nodes)
        return source_nodes

    def find_assign_final_sources(self, cpg_node: dict):
        # 返回赋值语句最右边的数据.e.g.String name1 = name2 = name3 = "test"; 返回"test"
        source_nodes = self.find_assign_sources(cpg_node)
        if source_nodes:
            return source_nodes[-1]
        else:
            return None
# ======================================== Assignment Functions End ========================================

# ======================================== Method Functions Start ========================================
    def get_method_full_name(self, cpg_node: dict):
        # 去除full name中的.<returnValue>
        method_full_name = cpg_node["methodFullName"]
        method_full_name = method_full_name.replace(".<returnValue>", "")
        return method_full_name
    
    def find_method_call_receivers(self, cpg_node: dict):
        # 找到函数调用的接收者
        node_id = cpg_node["id"]
        receiver_nodes = self.find_nodes(
            cpg_type = "call",
            conditions = [f"node.id=={str(node_id)}"],
            restricts = ["receiver"]
        )
        return receiver_nodes

    def find_parent_class_name(self, receiver_name: str):
        # 找到类的父类名称
        parent_names = self.find_nodes(
            cpg_type = "typeDecl",
            conditions = [f'node.name=="{receiver_name}"'],
            restricts = ["inheritsFromTypeFullName"]
        )
        return parent_names

    def get_all_parent_class_name(self, receiver_name: str):
        # 获取一个类的所有父类
        all_class_names = list()
        processed_names = list()
        processed_names.append(receiver_name)
        parent_names = self.find_parent_class_name(receiver_name)
        if parent_names:
            all_class_names.extend(parent_names)
            for parent_name in parent_names:
                if parent_name not in processed_names:
                    all_class_names.extend(self.get_all_parent_class_name(parent_name))
                    processed_names.append(parent_name)
        if receiver_name in all_class_names:
            all_class_names.remove(receiver_name)
        return all_class_names
    
    def check_full_name(self, method_full_name):
        # 检查函数全名是否存在
        method_full_name = method_full_name.replace(".<returnValue>", "")
        method_nodes = self.find_nodes(
            cpg_type = "method",
            conditions = [f'node.fullName == "{method_full_name}"'],
            restricts = []
        )
        if method_nodes != []:
            return True
        return False

    def get_method_real_full_name(self, cpg_node: dict):
        # 派生函数以获取真实的full name
        method_full_name = cpg_node["methodFullName"].replace(".<returnValue>", "")
        if not self.check_full_name(method_full_name):
            receiver_nodes = self.find_method_call_receivers(cpg_node)
            for receiver_node in receiver_nodes:
                if "typeFullName" in receiver_node.keys():
                    receiver_name = receiver_node["typeFullName"]
                    all_parent_names = self.get_all_parent_class_name(receiver_name)
                    for parent_name in all_parent_names:
                        new_method_full_name = method_full_name.replace(receiver_name, parent_name)
                        if self.check_full_name(new_method_full_name):
                            return new_method_full_name # 当新构造的函数名称能访问时,说明找到了合适的函数名称
        self.log_manager.log_info(f"Get Real Full Name: {method_full_name}", False, self.log_level)
        return method_full_name

    def get_method_short_name(self, cpg_node: dict):
        method_full_name = "None"
        if "methodFullName" in cpg_node.keys():
            method_full_name = cpg_node["methodFullName"]
        elif "fullName" in cpg_node.keys():
            method_full_name = cpg_node["fullName"]
        method_full_name = method_full_name.replace(".<returnValue>", "")
        method_short_name = None
        if method_full_name.find(":") != -1:
            method_full_name = method_full_name[:method_full_name.find(":")]
        if method_full_name.find("->") != -1:
            method_short_name = method_full_name.split("->")[-1]
        else:
            method_short_name = method_full_name.split(".")[-1]
        return method_short_name
    
    def get_method_return_type(self, cpg_node: dict):
        '''获取函数的返回值类型'''
        method_full_name = self.get_method_full_name(cpg_node)
        method_return_nodes = self.find_nodes(
            cpg_type = "method",
            conditions = [f'node.fullName == "{method_full_name}"'],
            restricts = ["methodReturn"]
        )
        if method_return_nodes:
            method_return_node = method_return_nodes[0]
            if isinstance(method_return_node, dict):
                if "typeFullName" in method_return_node.keys():
                    return method_return_node["typeFullName"]
        return "ANY"
    
    def find_method_by_fullname(self, method_full_name: str):
        if method_full_name is None:
            return None
        method_full_name = method_full_name.replace(".<returnValue>", "")
        method_nodes = self.find_nodes(
            cpg_type = "method",
            conditions = [f'node.fullName == "{method_full_name}"'],
            restricts = []
        )
        if method_nodes:
            return method_nodes[0]
        else:
            return None

    def find_method_by_node_fullname(self, cpg_node: dict):
        method_full_name = self.get_method_full_name(cpg_node)
        method_nodes = self.find_nodes(
            cpg_type = "method",
            conditions = [f'node.fullName == "{method_full_name}"'],
            restricts = []
        )
        if method_nodes:
            return method_nodes[0]
        else:
            return None
    
    def find_switch_case(self, cpg_node: dict):
        # 获取Switch语句各个Case
        # 注意:返回的有一个节点是Switch语句的default分支节点
        nodes = list()
        jump_target_nodes = self.find_cfgOut(cpg_node)
        for jump_target_node in jump_target_nodes:
            if jump_target_node["_label"] == "JUMP_TARGET":
                if jump_target_node["name"] == "case":
                    case_nodes = self.find_cfgOut(jump_target_node)
                    if case_nodes:
                        nodes.append(case_nodes[0])
                elif jump_target_node["name"] == "default":
                    nodes.append(jump_target_node)
        return nodes

    def find_method_parent(self, cpg_node: dict, gap_num: int):
        # 向上查找函数的父节点,gap_num代表层级数量
        gaps = list()
        for i in range(0, gap_num):
            gaps.append("astParent")
        method_full_name = self.get_method_full_name(cpg_node)
        method_parent_nodes = self.find_nodes(
            cpg_type = "method",
            conditions = [f'node.fullName == "{method_full_name}"'],
            restricts = gaps
        )
        if method_parent_nodes:
            return method_parent_nodes[0]
        return None
    
    def find_method_call_arguments(self, cpg_node: dict):
        # 查找函数调用的实参列表
        node_id = cpg_node["id"]
        nodes = self.find_nodes(
            cpg_type = "call",
            conditions = [f"node.id=={str(node_id)}"],
            restricts = ["argument"]
        )
        argument_nodes = self.check_block(nodes)
        return argument_nodes
    
    def find_method_parameters(self, cpg_node: dict):
        # 查找函数调用对应的函数定义时的形参列表
        method_full_name = cpg_node["methodFullName"]
        method_full_name = method_full_name.replace(".<returnValue>", "")
        parameter_nodes = self.find_nodes(
            cpg_type = "method",
            conditions = [f'node.fullName == "{method_full_name}"'],
            restricts = ["parameter"]
        )
        return parameter_nodes

    def is_obj_call(self, cpg_node: dict):
        '''判断函数调用是否是类的函数(检查上三辈)'''
        for gap_num in range(1, 4):
            method_parent_node = self.find_method_parent(cpg_node, gap_num)
            if method_parent_node:
                if isinstance(method_parent_node, dict):
                    if method_parent_node["_label"].strip() == "TYPE_DECL":
                        return True
            else:
                break
        return False

    def is_common_call(self, cpg_node: dict):
        '''判断函数调用是否是普通函数'''
        # 根据cpg_node["_label"]是否为"METHOD", "NAMESPACE_BLOCK"不足以判断函数类型
        for gap_num in range(1, 4):
            method_parent_node = self.find_method_parent(cpg_node, gap_num)
            if method_parent_node and isinstance(method_parent_node, dict):
                if method_parent_node["_label"].strip() == "TYPE_DECL":
                    return False
            else:
                break
        return True

    def is_external(self, cpg_node: dict):
        '''判断函数是否是外部函数( e.g. addslashes()就是一个外部函数 )'''
        external_flag = False
        real_full_name = None
        if cpg_node is not None:
            real_full_name = self.get_method_real_full_name(cpg_node)
            method_node = self.find_method_by_fullname(real_full_name)
            # method_node = self.find_method_by_node_fullname(cpg_node)
            if method_node:
                if "isExternal" in method_node.keys():
                    external_flag = (str(method_node["isExternal"]).lower().strip() == "true")
            # 处理Joern未能解决的global函数
            if external_flag:
                global_short_name = self.get_method_short_name(cpg_node)
                if global_short_name != real_full_name:
                    global_method_node = self.find_method_by_fullname(global_short_name)
                    if global_method_node is not None and isinstance(global_method_node, dict):
                        if "astParentFullName" in global_method_node.keys():
                            if global_method_node["astParentFullName"].find("php:<global>") != -1:
                                if "isExternal" in global_method_node.keys():
                                    real_full_name = global_short_name
                                    external_flag = (str(global_method_node["isExternal"]).lower().strip() == "true")
        return external_flag, real_full_name
    
    def is_type_decl(self, cpg_node: dict):
        '''判断函数是否是class的定义函数'''
        # 首先根据函数名称来做简单的筛选
        if "code" in cpg_node.keys():
            short_code = cpg_node["code"]
            if short_code.find("(") != -1 and short_code.find(")") != -1:
                short_code = short_code[:short_code.find("(")]
            if short_code.find("new ") != -1:
                return True
            elif short_code.find(".") != -1 or short_code.find("->") != -1:
                return False
        # 然后根据函数名称定义处做判断
        method_node = self.find_method_by_node_fullname(cpg_node)
        if method_node:
            if "isExternal" in method_node.keys():
                if str(method_node["isExternal"]).strip() == "false":
                    if "astParentType" in method_node.keys():
                        return (method_node["astParentType"].strip() == "TYPE_DECL")
        return False

    def find_call_edge_successors(self, real_full_name: str):
        # 找到函数调用的CFG子节点
        nodes = list()
        method_cpg_id = None
        method_node = self.find_method_by_fullname(real_full_name)
        if isinstance(method_node, dict):
            if "id" in method_node.keys():
                method_cpg_id = method_node["id"]
                cfg_out_call_nodes = self.find_cfgOut_until_call(method_node, False)
                for node in cfg_out_call_nodes:
                    nodes.append(self.find_astParent_until_top(node))
        successors = self.remove_duplicate_nodes(nodes)
        return method_cpg_id, successors
# ======================================== Method Functions End ========================================

# ======================================== Process PHP Magic Constant Start ========================================
    def is_magic_var(self, stmt_data: ObjField):
        # 判断变量是否是PHP的魔术变量
        var = None
        obj_var = None
        if stmt_data is not None:
            if stmt_data.node_type == "Object_Field":
                if hasattr(stmt_data, 'code'):
                    var = stmt_data.code
                if var is None and hasattr(stmt_data, 'identifier'):
                    var = stmt_data.identifier
                if stmt_data.obj is not None:
                    if hasattr(stmt_data.obj, 'code'):
                        obj_var = stmt_data.obj.code
                    if obj_var is None and hasattr(stmt_data.obj, 'identifier'):
                        obj_var = stmt_data.obj.identifier
                if var is not None and obj_var is not None:
                    if var.startswith("__") and var.endswith("__") and obj_var.find("<global>") != -1:
                        return True, var
        return False, None

    def process_magic_var(self, cpg_node: dict, var: str):
        node_type = "str"
        node_value = cpg_node["code"]
        literal = Literal(type = node_type, value = node_value)
        if var == "__DIR__":
            _, abs_path, _ = self.find_path_line(cpg_node["id"])
            if abs_path is not None:
                literal.value = os.path.dirname(abs_path)
        elif var == "__FILE__":
            _, literal.value, _ = self.find_path_line(cpg_node["id"])
        elif var == "__LINE__":
            literal.type = "int"
            _, _, literal.value = self.find_path_line(cpg_node["id"])
        elif var == "__CLASS__":
            class_node = self.find_belong_class(cpg_node)
            if isinstance(class_node, dict):
                literal.value = class_node["fullName"]
        elif var == "__FUNCTION__":
            method_node = self.find_belong_method(cpg_node)
            if isinstance(method_node, dict):
                if "name" in method_node.keys():
                    literal.value = method_node["name"]
        elif var == "__METHOD__":
            method_name = ""
            class_node = self.find_belong_class(cpg_node)
            if isinstance(class_node, dict):
                method_name = class_node["fullName"]
            method_node = self.find_belong_method(cpg_node)
            if method_name:
                if isinstance(method_node, dict):
                    if "name" in method_node.keys():
                        method_name = method_name + "::" + method_node["name"]
                        literal.value = method_name
        return literal
# ======================================== Process PHP Magic Constant End ========================================

# ======================================== Statement Process Start ========================================        
    def create_obj(self, cpg_node: dict):
        # 创建一个Obj
        obj = Obj(
            cpg_id = cpg_node["id"],
            code = cpg_node["code"],
            class_type = cpg_node["typeFullName"].replace(".<returnValue>", ""),
            identifier = cpg_node["code"] # TODO:name/code?
        )
        return obj

    def create_variable(self, cpg_node: dict):
        # 创建一个Variable
        variable = Variable(
            cpg_id = cpg_node["id"],
            code = cpg_node["code"],
            type = cpg_node["typeFullName"].replace(".<returnValue>", ""),
            identifier = cpg_node["code"] # TODO:name/code?
        )
        return variable
    
    def process_identifier(self, cpg_node: dict):
        # 处理标识符
        type_name = cpg_node["typeFullName"].replace(".<returnValue>", "")
        if type_name in self.variable_types:
            return self.create_variable(cpg_node)
        else:
            return self.create_obj(cpg_node)

    def process_obj_field(self, cpg_node: dict):
        # 处理对象属性
        obj_field = ObjField()
        obj_field.code = cpg_node["code"]
        obj_field.cpg_id = cpg_node["id"]
        child_nodes = self.find_astChildren(cpg_node)
        for node in child_nodes:
            if node["_label"] == "IDENTIFIER":
                obj_field.obj = self.create_obj(node)
            elif node["_label"] == "FIELD_IDENTIFIER":
                obj_field.type = cpg_node["typeFullName"].replace(".<returnValue>", "")
                obj_field.identifier = node["code"] # node["name"]
            elif node["_label"] == "<operator>.fieldAccess":
                obj_field.obj = self.process_obj_field(node) # 处理 stu.classmate.name = "CCC"; 这种情况 
        obj_field.update_signature()
        is_magic, var = self.is_magic_var(obj_field)
        if is_magic:
            return self.process_magic_var(cpg_node, var)
        return obj_field

    def process_literal(self, cpg_node: dict):
        # 处理字面量
        # TODO:目前只对 int,float,str,bool 4种类型进行了转换,未来可能需要处理更多类型
        node_type = cpg_node["typeFullName"].replace(".<returnValue>", "")
        node_value = cpg_node["code"]
        if node_type.find("char[") != -1 and node_type.find("]") != -1:
            node_type = "char[]"
        if node_type in self.type_map.keys():
            if self.type_map[node_type] == "int":
                node_value = node_value.replace("//\n", "")
                node_value = int(node_value)
            elif self.type_map[node_type] == "float":
                node_value = node_value.replace("//\n", "")
                node_value = float(node_value)
            elif self.type_map[node_type] == "str":
                node_value = str(node_value).strip('\"').strip("\'").strip('"').strip("'")
            elif self.type_map[node_type] == "bool":
                if node_value.lower().find("true") != -1:
                    node_value = True
                elif node_value.lower().find("false") != -1:
                    node_value = False
                else:
                    node_value = bool(node_value)
        literal = Literal(
            type = node_type,
            value = node_value
        )
        return literal

    def process_operation(self, cpg_node: dict):
        # 处理数据操作
        operation = Operation()
        operation.code = cpg_node["code"]
        operation.cpg_id = cpg_node["id"]
        operation.operator = cpg_node["methodFullName"]
        child_nodes = self.find_astChildren(cpg_node)
        for node in child_nodes:
            operation.operands.append(self.parse_stmt(node))
        return operation
    
    def process_assignment(self, cpg_node: dict):
        # 处理赋值语句(已处理=, +=, .=, -=, *=, /=, %=等赋值运算)
        assign = Assign()
        assign.code = cpg_node["code"]
        assign.cpg_id = cpg_node["id"]
        if cpg_node["methodFullName"].strip() == "<operator>.assignment":
            target_nodes = self.find_assign_targets(cpg_node)
            for node in target_nodes:
                target = self.parse_stmt(node)
                if target is not None:
                    assign.LValues.append(target)
            source_node = self.find_assign_final_sources(cpg_node)
            assign.RValue = self.parse_stmt(source_node)
        else:
            operation = Operation()
            operation.code = cpg_node["code"]
            operation.cpg_id = cpg_node["id"]
            operation.operator = cpg_node["methodFullName"]
            child_nodes = self.find_astChildren(cpg_node)
            for i in range(0, len(child_nodes)):
                node = child_nodes[i]
                node_stmt = self.parse_stmt(node)
                if node_stmt is not None:
                    operation.operands.append(node_stmt)
                    if i == 0:
                        assign.LValues.append(node_stmt)
            assign.RValue = operation
        return assign

    def process_method(self, cpg_node: dict, obj: Obj):
        # 处理函数定义
        method = Method()
        if obj is not None:
            method.node_type = "ObjMethod"
            method.obj_name = obj.class_type
        else:
            method.node_type = "CommonMethod"
        method.fullName = self.get_method_full_name(cpg_node)
        method.shotName = self.get_method_short_name(cpg_node)
        method.methodReturn = self.get_method_return_type(cpg_node)
        parameter_nodes = self.find_method_parameters(cpg_node)
        for node in parameter_nodes:
            method.parameter_types.append(node["typeFullName"])
            parameter_index1 = node["name"]
            parameter_index2 = str(node["index"])
            parameter = self.parse_stmt(node)
            if parameter is not None:
                method.parameters[parameter_index1] = parameter
                method.parameters[parameter_index2] = parameter
        method.update_signature()
        return method

    def process_obj_call(self, cpg_node: dict):
        # 处理类的函数调用
        obj_call = ObjCall()
        obj_call.code = cpg_node["code"]
        obj_call.cpg_id = cpg_node["id"]
        obj_call.fullName = self.get_method_full_name(cpg_node)
        argument_nodes = self.find_method_call_arguments(cpg_node)
        for node in argument_nodes:
            if str(node["argumentIndex"]) == "0":
                obj_call.obj = self.create_obj(node)
                obj_call.arguments["0"] = obj_call.obj
            else:
                argument_index = node["argumentIndex"]
                if argument_index == "-1" and "argumentName" in node.keys():
                    argument_index = node["argumentName"]
                argument = self.parse_stmt(node)
                obj_call.arguments[str(argument_index)] = argument
        obj_call.method = self.process_method(cpg_node, obj_call.obj)
        return obj_call

    def process_common_call(self, cpg_node: dict):
        # 处理普通函数调用 (为了防止误判为普通函数调用,还需要检查参数中的argumentIndex是否为0)
        misjudge = False
        argument_nodes = self.find_method_call_arguments(cpg_node)
        for node in argument_nodes:
            if isinstance(node, dict):
                if "argumentIndex" in node.keys():
                    if str(node["argumentIndex"]) == "0":
                        misjudge = True
                        break
        if misjudge:
            return self.process_obj_call(cpg_node)
        common_call = CommonCall()
        common_call.code = cpg_node["code"]
        common_call.cpg_id = cpg_node["id"]
        common_call.fullName = self.get_method_full_name(cpg_node)
        argument_nodes = self.find_method_call_arguments(cpg_node)
        for node in argument_nodes:
            argument_index = node["argumentIndex"]
            if argument_index == "-1" and "argumentName" in node.keys():
                argument_index = node["argumentName"]
            argument = self.parse_stmt(node)
            common_call.arguments[str(argument_index)] = argument
        common_call.method = self.process_method(cpg_node, None)
        return common_call

    def process_control_structure(self, cpg_node: dict):
        # 处理控制结构
        controlstructure = ControlStructure()
        controlstructure.cpg_id = cpg_node["id"]
        controlstructure.code = cpg_node["code"]
        controlstructure.controlStructureType = cpg_node["controlStructureType"]
        controlstructure.condition = self.parse_stmt(self.find_control_condition(cpg_node))
        return controlstructure

    def process_method_return(self, cpg_node: dict):
        # 处理函数返回值语句
        method_return = MethodReturn()
        method_return.cpg_id = cpg_node["id"]
        method_return.code = cpg_node["code"]
        cfgin_nodes = self.find_cfgIn(cpg_node)
        if cfgin_nodes:
            method_return.return_result = self.parse_stmt(cfgin_nodes[0])
        return method_return
    
    def process_type_cast(self, cpg_node: dict):
        # 处理强制类型转换语句
        temporary = Temporary()
        if isinstance(cpg_node, dict) and "typeFullName" in cpg_node.keys():
            temporary.type = cpg_node["typeFullName"]
            if temporary.type is not None:
                if temporary.type in self.type_map.keys():
                    temporary.type = self.type_map[temporary.type]
        return temporary

    def parse_stmt(self, cpg_node: dict):
        # 处理子节点,将其转换为对应的类
        temp_id = None
        temp_code = None
        if isinstance(cpg_node, dict):
            if "id" in cpg_node.keys():
                temp_id = cpg_node["id"]
                if "_label" in cpg_node.keys():
                    if cpg_node["_label"] == "CALL" and "methodFullName" not in cpg_node.keys():
                        cpg_node = self.find_cpg_node_by_id(temp_id)
            if "code" in cpg_node.keys():
                temp_code = cpg_node["code"]
        self.log_manager.log_info(f"Parsing CPG Node to Stmt: [cpg id:{temp_id}] [code:{temp_code}]", False, self.log_level)
        if cpg_node:
            if cpg_node["_label"] == "CALL":
                if cpg_node["methodFullName"].find("<operator>.") != -1:
                    if cpg_node["methodFullName"].strip().find("<operator>.assignment") != -1:
                        return self.process_assignment(cpg_node)
                    elif cpg_node["methodFullName"].strip() == "<operator>.fieldAccess":
                        return self.process_obj_field(cpg_node)
                    elif cpg_node["methodFullName"].strip() == "<operator>.alloc":
                        if cpg_node["typeFullName"] in self.variable_types:
                            return self.process_literal(cpg_node)
                        else:
                            return self.create_obj(cpg_node) # TODO:这里具体应该采用什么方法还不确定!
                    else:
                        return self.process_operation(cpg_node)
                elif self.is_type_decl(cpg_node):
                    return self.create_obj(cpg_node)
                elif self.is_obj_call(cpg_node):
                    return self.process_obj_call(cpg_node)
                elif self.is_common_call(cpg_node):
                    return self.process_common_call(cpg_node)
            elif cpg_node["_label"] == "LITERAL":
                return self.process_literal(cpg_node)
            elif cpg_node["_label"] in ["IDENTIFIER", "METHOD_PARAMETER_IN"]:
                return self.process_identifier(cpg_node)
            elif cpg_node["_label"] == "CONTROL_STRUCTURE":
                return self.process_control_structure(cpg_node)
            elif cpg_node["_label"] == "RETURN":
                return self.process_method_return(cpg_node)
            elif cpg_node["_label"] == "TYPE_REF":
                return self.process_type_cast(cpg_node)
        self.log_manager.log_info(f"Parsing CPG Node to Stmt ERROR: [cpg id:{temp_id}] [code:{temp_code}]", False, self.log_level)
        return None
# ======================================== Statement Process End ========================================
    
if __name__ == "__main__":
    logmanager = LogManager()
    config_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")), "config.json")
    with open(config_path, "r", encoding = "utf-8") as f:
        config_file = json.load(f)
    repo_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")), "test")
    joern_server = JoernServer(
        config_file = config_file, 
        repo_path = repo_path, 
        log_manager = logmanager,
        checkout_tag = "1.0"
    )
    start_cpg_nodes = joern_server.find_node_contain("Student s1 = new Student()") # CPG2Stmt/test/test_case.java第31行的赋值语句
    start_cpg_node = None
    if start_cpg_nodes:
        start_cpg_node = start_cpg_nodes[0]
    workstack = list()
    if isinstance(start_cpg_node, dict):
        workstack.append(start_cpg_node)
    visited = list()
    while workstack != []:
        node = workstack.pop()
        if isinstance(node, dict) and "id" in node.keys():
            if node["id"] not in visited:
                visited.append(node["id"])
                stmt = joern_server.parse_stmt(node)
                if stmt is not None:
                    print(stmt.to_string())
                    input()
                successors = joern_server.find_cfg_successors(node)
                for successor in successors:
                    if isinstance(successor, dict):
                        workstack.append(successor)
    joern_server.close_cpg()