# ast_nodes.py

class Node:
    pass


class Program(Node):
    def __init__(self, procedures, main):
        self.procedures = procedures
        self.main = main


class Procedure(Node):
    def __init__(self, head, declarations, commands):
        self.name = head[0]
        self.args = head[1]  # Lista krotek (typ, nazwa)
        self.declarations = declarations
        self.commands = commands


class Main(Node):
    def __init__(self, declarations, commands):
        self.declarations = declarations
        self.commands = commands

# --- Deklaracje ---


class Variable(Node):
    def __init__(self, name):
        self.name = name


class ArrayDecl(Node):
    def __init__(self, name, start, end):
        self.name = name
        self.start = start
        self.end = end


class Number(Node):
    def __init__(self, value):
        self.value = value

# --- Komendy ---


class Assign(Node):
    def __init__(self, identifier, expression):
        self.identifier = identifier
        self.expression = expression


class ArrayAssign(Node):
    def __init__(self, name, index, expression):
        self.name = name
        self.index = index
        self.expression = expression


class If(Node):
    def __init__(self, condition, commands_then, commands_else=None):
        self.condition = condition
        self.commands_then = commands_then
        self.commands_else = commands_else


class While(Node):
    def __init__(self, condition, commands):
        self.condition = condition
        self.commands = commands


class Repeat(Node):
    def __init__(self, commands, condition):
        self.commands = commands
        self.condition = condition


class For(Node):
    def __init__(self, iterator, start_expr, end_expr, commands, downto=False):
        self.iterator = iterator
        self.start_expr = start_expr
        self.end_expr = end_expr
        self.commands = commands
        self.downto = downto


class ProcCall(Node):
    def __init__(self, name, args):
        self.name = name
        self.args = args  # Lista wartości/zmiennych przekazywanych


class Read(Node):
    def __init__(self, identifier):
        self.identifier = identifier


class Write(Node):
    def __init__(self, value):
        self.value = value

# --- Wyrażenia ---


class BinOp(Node):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right


class Condition(Node):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right


class ArrayRef(Node):
    def __init__(self, name, index):
        self.name = name
        self.index = index
