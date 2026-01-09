# parser.py
from sly import Parser
from lexer import KompilatorLexer
# Importujemy nasze klasy AST
from ast_nodes import Program, Procedure, Main, Variable, Array


# --- Hack dla Pylance (dodaj to, aby usunąć błędy "_ is not defined") ---
def _(rule):
    def decorator(f):
        f.rule = rule  # Przypisujemy regułę, żeby wszystko działało poprawnie
        return f
    return decorator
# -----------------------------------------------------------------------


class KompilatorParser(Parser):
    tokens = KompilatorLexer.tokens

    # --- Gramatyka (Tabela 1) ---

    # 1. program_all -> procedures main
    @_('procedures main')
    def program_all(self, p):
        return Program(p.procedures, p.main)

    # 2. procedures -> procedures PROCEDURE proc_head IS declarations IN commands END
    #              | procedures PROCEDURE proc_head IS IN commands END
    #              | (puste)
    @_('procedures PROCEDURE proc_head IS declarations IN commands END')
    def procedures(self, p):
        # p.procedures to lista z poprzedniej rekurencji. Dodajemy nową procedurę.
        new_proc = Procedure(
            p.proc_head['name'], p.proc_head['args'], p.declarations, p.commands)
        p.procedures.append(new_proc)
        return p.procedures

    @_('procedures PROCEDURE proc_head IS IN commands END')
    def procedures(self, p):
        # Wersja bez deklaracji zmiennych lokalnych
        new_proc = Procedure(
            p.proc_head['name'], p.proc_head['args'], [], p.commands)
        p.procedures.append(new_proc)
        return p.procedures

    @_('')
    def procedures(self, p):
        return []  # Baza rekurencji: brak procedur to pusta lista

    # 3. main -> PROGRAM IS declarations IN commands END
    #         | PROGRAM IS IN commands END
    @_('PROGRAM IS declarations IN commands END')
    def main(self, p):
        return Main(p.declarations, p.commands)

    @_('PROGRAM IS IN commands END')
    def main(self, p):
        return Main([], p.commands)

    # --- Pomocnicze (zaślepki, żeby kod działał, rozwiniemy je za chwilę) ---

    @_('PIDENTIFIER LPAREN args_decl RPAREN')
    def proc_head(self, p):
        return {'name': p.PIDENTIFIER, 'args': p.args_decl}

    @_('')
    def args_decl(self, p):
        return []

    @_('')
    def declarations(self, p):
        return []

    @_('')
    def commands(self, p):
        return []

    # Obsługa błędów składniowych
    def error(self, p):
        if p:
            print(
                f"Błąd składniowy przy tokenie '{p.value}' w linii {p.lineno}")
        else:
            print("Błąd składniowy: Nieoczekiwany koniec pliku")


# Kod testowy
if __name__ == '__main__':
    lexer = KompilatorLexer()
    parser = KompilatorParser()

    text = """
    PROCEDURE test( ) IS IN END
    PROGRAM IS IN END
    """

    tokens = lexer.tokenize(text)
    result = parser.parse(tokens)
    print("Wynik parsowania:", result)
