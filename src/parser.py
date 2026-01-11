from sly import Parser
from lexer import KompilatorLexer
# Upewnij się, że masz zaimportowane wszystkie węzły
from ast_nodes import *


class KompilatorParser(Parser):
    tokens = KompilatorLexer.tokens

    # --- Priorytety operatorów ---
    # Im niżej na liście, tym wyższy priorytet (mnożenie wiąże mocniej niż dodawanie)
    precedence = (
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIV', 'MOD'),
    )

    # --- Program Structure (bez zmian) ---
    @_('procedures main')
    def program_all(self, p):
        return Program(p.procedures, p.main)

    @_('')
    def procedures(self, p):
        return []

    @_('PROGRAM IS declarations IN commands END')
    def main(self, p):
        return Main(p.declarations, p.commands)

    # --- Declarations (bez zmian) ---
    @_('declarations COMMA PIDENTIFIER')
    def declarations(self, p):
        p.declarations.append(p.PIDENTIFIER)
        return p.declarations

    @_('PIDENTIFIER')
    def declarations(self, p):
        return [p.PIDENTIFIER]

    @_('')
    def declarations(self, p):
        return []

    # --- Commands (bez zmian + dodane READ z poprzedniego kroku) ---
    @_('commands command')
    def commands(self, p):
        p.commands.append(p.command)
        return p.commands

    @_('command')
    def commands(self, p):
        return [p.command]

    @_('PIDENTIFIER ASSIGN expression SEMICOLON')
    def command(self, p):
        return Assign(p.PIDENTIFIER, p.expression)

    @_('WRITE value SEMICOLON')
    def command(self, p):
        return Write(p.value)

    @_('READ PIDENTIFIER SEMICOLON')
    def command(self, p):
        return Read(p.PIDENTIFIER)

    # Instrukcje sterujące (IF, WHILE, REPEAT - te, które dodaliśmy wcześniej)
    @_('IF condition THEN commands ELSE commands ENDIF')
    def command(self, p):
        return If(p.condition, p.commands0, p.commands1)

    @_('IF condition THEN commands ENDIF')
    def command(self, p):
        return If(p.condition, p.commands, None)

    @_('WHILE condition DO commands ENDWHILE')
    def command(self, p):
        return While(p.condition, p.commands)

    @_('REPEAT commands UNTIL condition SEMICOLON')
    def command(self, p):
        return Repeat(p.commands, p.condition)

    # --- Conditions (bez zmian) ---
    @_('value EQ value', 'value NEQ value',
       'value GT value', 'value LT value',
       'value GE value', 'value LE value')
    def condition(self, p):
        return Condition(p.value0, p[1], p.value1)

    # --- Expressions (TUTAJ JEST KLUCZOWA ZMIANA) ---
    @_('value')
    def expression(self, p):
        return p.value

    # Dodajemy obsługę wszystkich operatorów arytmetycznych
    @_('value PLUS value',
       'value MINUS value',
       'value TIMES value',
       'value DIV value',
       'value MOD value')
    def expression(self, p):
        # p[1] to operator (+, -, *, /, %) jako string
        return BinOp(p.value0, p[1], p.value1)

    # --- Values (bez zmian) ---
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
