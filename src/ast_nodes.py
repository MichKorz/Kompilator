# ast_nodes.py

class Node:
    """Bazowa klasa dla wszystkich węzłów AST"""
    pass


class Program(Node):
    def __init__(self, procedures, main):
        self.procedures = procedures  # Lista procedur
        self.main = main             # Główna część programu (Main)

    def __repr__(self):
        return f"Program(procs={len(self.procedures)}, main={self.main})"


class Procedure(Node):
    def __init__(self, name, args, declarations, commands):
        self.name = name
        self.args = args             # Lista argumentów
        self.declarations = declarations  # Zmienne lokalne
        self.commands = commands     # Lista komend

    def __repr__(self):
        return f"Proc {self.name}(args={self.args})"


class Main(Node):
    def __init__(self, declarations, commands):
        self.declarations = declarations
        self.commands = commands

    def __repr__(self):
        return "MainProgram"

# Struktury dla zmiennych (potrzebne do deklaracji)


class Variable(Node):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"Var({self.name})"


class Array(Node):
    def __init__(self, name, start, end):
        self.name = name
        self.start = start
        self.end = end

    def __repr__(self):
        return f"Arr({self.name}[{self.start}:{self.end}])"

# --- Komendy ---


class Assign(Node):
    def __init__(self, identifier, expression):
        self.identifier = identifier  # Nazwa zmiennej (string)
        self.expression = expression  # Co przypisujemy (Node)

    def __repr__(self):
        return f"{self.identifier} := {self.expression}"


class Write(Node):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"WRITE {self.value}"

# --- Wyrażenia ---


class BinOp(Node):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

    def __repr__(self):
        return f"({self.left} {self.op} {self.right})"


class Number(Node):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return str(self.value)

# --- Vertical slice 2 --- #


class Condition(Node):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

    def __repr__(self):
        return f"Cond({self.left} {self.op} {self.right})"


class If(Node):
    def __init__(self, condition, commands_then, commands_else=None):
        self.condition = condition
        self.commands_then = commands_then  # Lista komend
        self.commands_else = commands_else  # Lista komend lub None

    def __repr__(self):
        else_part = " ELSE ..." if self.commands_else else ""
        return f"IF {self.condition} THEN ...{else_part} ENDIF"


class While(Node):
    def __init__(self, condition, commands):
        self.condition = condition
        self.commands = commands

    def __repr__(self):
        return f"WHILE {self.condition} DO ..."


class Repeat(Node):
    def __init__(self, commands, condition):
        self.commands = commands
        self.condition = condition

    def __repr__(self):
        return f"REPEAT ... UNTIL {self.condition}"


class Read(Node):
    def __init__(self, identifier):
        self.identifier = identifier

    def __repr__(self):
        return f"READ {self.identifier}"
