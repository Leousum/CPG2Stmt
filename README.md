# CPG2Stmt简介

**why CPG2Stmt？** 在使用[Joern](https://github.com/joernio/joern)提供的CPG过程中，我们发现CPG并不利于进行后续的静态程序分析，原因主要在于[Joern](https://github.com/joernio/joern)没有提供方便程序分析的接口（例如未提供查找CFG后继节点功能）。因此，我们自行设计了一套方便程序分析的统一代码表示： **Stmt** ，并在此基础上提供了多个接口。目前，我们在 **Stmt** 基础上实现了 **基于指针分析的污点分析**、 **符号执行** 、 **稀疏分析** 、 **可复用的持久化摘要** 等功能（此仓库中不展示）。

**what is CPG2Stmt？** 本仓库 **CPG2Stmt** 能够将Joern解析源代码得到的CPG转换为统一表示： **Stmt** ，具体来说，我们提供了赋值语句、类函数调用、普通函数调用、函数定义、函数返回、对象、变量、对象属性、字面量、数据操作、临时变量以及控制结构共计12种类型的 **Stmt** ，它能够有效表示源代码的原本结构，适用于进行多语言程序分析。

# 安装与使用

(1)安装Joern，按照[Joern官网](https://docs.joern.io/installation/)提供的命令即可完成安装：

```bash
mkdir joern && cd joern # optional
curl -L "https://github.com/joernio/joern/releases/latest/download/joern-install.sh" -o joern-install.sh
chmod u+x joern-install.sh
./joern-install.sh --interactive
```

(2)修改配置文件

完成Joern的安装后，我们需要修改[config.json](/config.json)配置文件中的"`joern_server_point`"，我们默认其`host`为`localhost`，`port`为`8989`。用户可以修改为其它可用的端口，以避免产生冲突。

(3)安装python环境与依赖库

**CPG2Stmt** 由python编写而成，在测试其功能前，用户需要安装 **python 3.x** 环境， 同时还需要通过以下命令安装依赖库：

```shell
pip install -r requirements.txt
```

(4)测试CPG2Stmt

我们提供了一个Java语言编写的测试程序[test_case.java](./test/test_case.java)，并在[joern.py](joern.py)的`main`函数中展示了如何对此文件进行简单的程序分析。用户可以使用以下命令测试 **CPG2Stmt** ，它会从测试代码的第31行开始分析，分析结果会被打印、同时保存到[logs](logs)文件夹下的日志文件中。

```shell
python3 joern.py
```

**注意：** 首先，测试代码主要展现了 **Stmt** 的案例，我们还在AST、CFG、CG等结构上提供了适配于Stmt的接口，适用于进行过程间分析。此外，在[joern.py](joern.py)中提供了自行打开Joern服务的`start_joern_service()`函数和自行关闭Joern服务的`close_cpg()`函数，因此，用户无需自行打开/关闭Joern服务。我们与Joern交互是通过[cpgqls-client-python](https://github.com/joernio/cpgqls-client-python)提供的代码实现的，交互的主要逻辑是向Joern客户端发送查询语句，而后获取查询结果。最后，我们将使用Joern过程中所用到的查询语句和发现的问题记录在了 [Joern Document](Joern Document.pdf) 中，希望能够为各位提供一定的帮助。

### Stmt案例

以下面这行源代码为例：

```java
int z = x + y;
```

其 **Stmt** 结构为:

```python
----------------------------------------------
| node_type: Assignment
| cpg_id: 261
| code: int z = x + y
| LValues: 
    | LValues[0]:
        ----------------------------------------------
        | node_type: Variable
        | cpg_id: 262
        | code: z
        | type: int
        | identifier: z
        | value: None
        | signature: <[Variable]: int: z>
        ----------------------------------------------
| RValue: 
    ----------------------------------------------
    | node_type: Operation
    | cpg_id: 263
    | code: x + y
    | operator: <operator>.addition
    | operands: 
        | operands[0]:
            ----------------------------------------------
            | node_type: Variable
            | cpg_id: 264
            | code: x
            | type: int
            | identifier: x
            | value: None
            | signature: <[Variable]: int: x>
            ----------------------------------------------
        | operands[1]:
            ----------------------------------------------
            | node_type: Variable
            | cpg_id: 265
            | code: y
            | type: int
            | identifier: y
            | value: None
            | signature: <[Variable]: int: y>
            ----------------------------------------------
    ----------------------------------------------
----------------------------------------------
```

其中`Assignment`表示整体为一个赋值语句，`LValues`代表赋值语句的左端，由于可能会存在多个左值，例如`x = y = z = 1;`，因此，`LValues`是一个数组，其中可能包含了多个元素。`RValue`代表赋值语句的右端，这里的赋值语句右端是一个`Operation`类型的Stmt，代表数据操作`x+y`。而这个数据操作的具体操作类型为`<operator>.addition`，表示相加操作，其操作数为两个`Variable`类型的变量`x`和`y`。
