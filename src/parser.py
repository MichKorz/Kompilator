# parser.py
from sly import Parser
from lexer import KompilatorLexer
from ast_nodes import *


class KompilatorParser(Parser):
    tokens = KompilatorLexer.tokens

    # Priorytety operatorów (rozwiązują konflikty shift/reduce)
    precedence = (
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIV', 'MOD'),
    )

    # --- Program Structure ---
    @_('procedures main')
    def program_all(self, p):
        return Program(p.procedures, p.main)

    @_('')
    def procedures(self, p):
        return []  # Na razie ignorujemy procedury dla MVP

    @_('PROGRAM IS declarations IN commands END')
    def main(self, p):
        return Main(p.declarations, p.commands)

    # --- Declarations (uproszczone: tylko zmienne, bez tablic na razie) ---
    @_('declarations COMMA PIDENTIFIER')
    def declarations(self, p):
        p.declarations.append(p.PIDENTIFIER)
        return p.declarations

    @_('PIDENTIFIER')
    def declarations(self, p):
        return [p.PIDENTIFIER]

    # Obsługa pustych deklaracji (jeśli dozwolone) lub błędów
    @_('')
    def declarations(self, p):
        return []

    # --- Commands ---
    @_('commands command')
    def commands(self, p):
        p.commands.append(p.command)
        return p.commands

    @_('command')
    def commands(self, p):
        return [p.command]

    # Pojedyncza komenda: Przypisanie
    @_('PIDENTIFIER ASSIGN expression SEMICOLON')
    def command(self, p):
        return Assign(p.PIDENTIFIER, p.expression)

    # Pojedyncza komenda: WRITE
    @_('WRITE value SEMICOLON')
    def command(self, p):
        return Write(p.value)

    # --- Expressions ---
    @_('value')
    def expression(self, p):
        return p.value

    @_('value PLUS value')
    def expression(self, p):
        return BinOp(p.value0, '+', p.value1)

    # Inne operatory dodasz tutaj później...

    # --- Values ---
    @_('NUM')
    def value(self, p):
        return Number(p.NUM)

    @_('PIDENTIFIER')
    def value(self, p):
        return Variable(p.PIDENTIFIER)

    def error(self, p):
        if p:
            print(f"Błąd składniowy: '{p.value}' w linii {p.lineno}")
        else:
            print("Nieoczekiwany koniec pliku")
