from sly import Parser
from lexer import KompilatorLexer
from ast_nodes import *


class KompilatorParser(Parser):
    tokens = KompilatorLexer.tokens

    precedence = (
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIV', 'MOD'),
    )

    # --- Struktura Programu ---
    @_('procedures main')
    def program_all(self, p):
        return Program(p.procedures, p.main)

    @_('procedures PROCEDURE proc_head IS declarations IN commands END')
    def procedures(self, p):
        p.procedures.append(Procedure(p.proc_head, p.declarations, p.commands))
        return p.procedures

    @_('PROCEDURE proc_head IS declarations IN commands END')
    def procedures(self, p):
        return [Procedure(p.proc_head, p.declarations, p.commands)]

    @_('')
    def procedures(self, p):
        return []

    # Nagłówek procedury
    @_('PIDENTIFIER LPAREN args_decl RPAREN')
    def proc_head(self, p):
        return (p.PIDENTIFIER, p.args_decl)

    # Argumenty deklaracji (w nagłówku procedury)
    @_('args_decl COMMA arg_decl')
    def args_decl(self, p):
        p.args_decl.append(p.arg_decl)
        return p.args_decl

    @_('arg_decl')
    def args_decl(self, p):
        return [p.arg_decl]

    @_('')
    def args_decl(self, p):
        return []

    # Typy argumentów - tu używamy tokenów T, I, O
    @_('T PIDENTIFIER')
    def arg_decl(self, p):
        return ('T', p.PIDENTIFIER)

    @_('I PIDENTIFIER')
    def arg_decl(self, p):
        return ('I', p.PIDENTIFIER)

    @_('O PIDENTIFIER')
    def arg_decl(self, p):
        return ('O', p.PIDENTIFIER)

    # Zwykła zmienna (jeśli język na to pozwala w arg)
    @_('PIDENTIFIER')
    def arg_decl(self, p):
        return ('VAR', p.PIDENTIFIER)

    # --- Main ---
    @_('PROGRAM IS declarations IN commands END')
    def main(self, p):
        return Main(p.declarations, p.commands)

    # --- Deklaracje Zmiennych (IS ... IN) ---
    @_('declarations COMMA PIDENTIFIER')
    def declarations(self, p):
        p.declarations.append(p.PIDENTIFIER)
        return p.declarations

    @_('declarations COMMA PIDENTIFIER LBRACKET NUM COLON NUM RBRACKET')
    def declarations(self, p):
        p.declarations.append(ArrayDecl(p.PIDENTIFIER, p.NUM0, p.NUM1))
        return p.declarations

    @_('PIDENTIFIER')
    def declarations(self, p):
        return [p.PIDENTIFIER]

    @_('PIDENTIFIER LBRACKET NUM COLON NUM RBRACKET')
    def declarations(self, p):
        return [ArrayDecl(p.PIDENTIFIER, p.NUM0, p.NUM1)]

    @_('')
    def declarations(self, p):
        return []

    # --- Komendy ---
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

    @_('PIDENTIFIER LBRACKET value RBRACKET ASSIGN expression SEMICOLON')
    def command(self, p):
        return ArrayAssign(p.PIDENTIFIER, p.value, p.expression)

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

    @_('FOR PIDENTIFIER FROM value TO value DO commands ENDFOR')
    def command(self, p):
        return For(p.PIDENTIFIER, p.value0, p.value1, p.commands, downto=False)

    @_('FOR PIDENTIFIER FROM value DOWNTO value DO commands ENDFOR')
    def command(self, p):
        return For(p.PIDENTIFIER, p.value0, p.value1, p.commands, downto=True)

    @_('PIDENTIFIER LPAREN args RPAREN SEMICOLON')
    def command(self, p):
        return ProcCall(p.PIDENTIFIER, p.args)

    @_('READ PIDENTIFIER SEMICOLON')
    def command(self, p):
        return Read(p.PIDENTIFIER)

    @_('WRITE value SEMICOLON')
    def command(self, p):
        return Write(p.value)

    # --- Argumenty wywołania procedury ---
    @_('args COMMA PIDENTIFIER')
    def args(self, p):
        p.args.append(Variable(p.PIDENTIFIER))
        return p.args

    @_('PIDENTIFIER')
    def args(self, p):
        return [Variable(p.PIDENTIFIER)]

    @_('')
    def args(self, p):
        return []

    # --- Warunki i Wyrażenia ---
    @_('value EQ value', 'value NEQ value',
       'value GT value', 'value LT value',
       'value GE value', 'value LE value')
    def condition(self, p):
        return Condition(p.value0, p[1], p.value1)

    @_('value')
    def expression(self, p):
        return p.value

    @_('value PLUS value', 'value MINUS value',
       'value TIMES value', 'value DIV value', 'value MOD value')
    def expression(self, p):
        return BinOp(p.value0, p[1], p.value1)

    @_('NUM')
    def value(self, p):
        return Number(p.NUM)

    @_('PIDENTIFIER')
    def value(self, p):
        return Variable(p.PIDENTIFIER)

    @_('PIDENTIFIER LBRACKET value RBRACKET')
    def value(self, p):
        return ArrayRef(p.PIDENTIFIER, p.value)

    def error(self, p):
        if p:
            print(f"Błąd składniowy: '{p.value}' w linii {p.lineno}")
        else:
            print("Nieoczekiwany koniec pliku")
