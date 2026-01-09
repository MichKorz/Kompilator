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
