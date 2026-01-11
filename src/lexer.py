from sly import Lexer


# --- Hack dla Pylance (dodaj to, aby usunąć błędy "_ is not defined") ---
def _(rule):
    def decorator(f):
        f.rule = rule  # Przypisujemy regułę, żeby wszystko działało poprawnie
        return f
    return decorator
# -----------------------------------------------------------------------


class KompilatorLexer(Lexer):
    tokens = {
        # Słowa kluczowe (jako stringi!)
        "PROCEDURE", "PROGRAM", "IS", "IN", "END",
        "IF", "THEN", "ELSE", "ENDIF",
        "WHILE", "DO", "ENDWHILE",
        "REPEAT", "UNTIL",
        "FOR", "FROM", "TO", "DOWNTO", "ENDFOR",
        "READ", "WRITE",

        "T",
        "PIDENTIFIER", "NUM",

        "PLUS", "MINUS", "TIMES", "DIV", "MOD",
        "ASSIGN", "EQ", "NEQ", "LE", "GE", "LT", "GT",
        "LPAREN", "RPAREN", "LBRACKET", "RBRACKET", "COLON", "SEMICOLON", "COMMA"
    }

    # Ignorujemy białe znaki
    ignore = ' \t'
    # Ignorujemy komentarze
    ignore_comment = r'\#.*'

    # --- Definicje Tokenów (Operatorów) --- (Regexs)
    ASSIGN = r':='
    NEQ = r'!='
    GE = r'>='
    LE = r'<='

    PLUS = r'\+'
    MINUS = r'-'
    TIMES = r'\*'
    DIV = r'/'
    MOD = r'%'
    EQ = r'='
    LT = r'<'
    GT = r'>'

    LPAREN = r'\('
    RPAREN = r'\)'
    LBRACKET = r'\['
    RBRACKET = r'\]'
    COLON = r':'
    SEMICOLON = r';'
    COMMA = r','

    # --- Liczby ---
    @_(r'\d+')
    def NUM(self, t):
        t.value = int(t.value)
        return t

    # --- Identyfikatory i Słowa Kluczowe ---
    # ZMIANA: Regex łapie teraz też duże litery [a-zA-Z_]+
    @_(r'[a-zA-Z_]+')
    def PIDENTIFIER(self, t):
        # Mapa słów kluczowych
        reserved = {
            'PROCEDURE': 'PROCEDURE', 'IS': 'IS', 'IN': 'IN', 'END': 'END',
            'PROGRAM': 'PROGRAM',
            'IF': 'IF', 'THEN': 'THEN', 'ELSE': 'ELSE', 'ENDIF': 'ENDIF',
            'WHILE': 'WHILE', 'DO': 'DO', 'ENDWHILE': 'ENDWHILE',
            'REPEAT': 'REPEAT', 'UNTIL': 'UNTIL',
            'FOR': 'FOR', 'FROM': 'FROM', 'TO': 'TO', 'DOWNTO': 'DOWNTO', 'ENDFOR': 'ENDFOR',
            'READ': 'READ', 'WRITE': 'WRITE',
            'T': 'T'  # Dodane T dla tablic (pkt 2 i 3 specyfikacji)
        }

        # Sprawdzamy czy to słowo kluczowe
        token_type = reserved.get(t.value)
        if token_type:
            t.type = token_type
        else:
            # Jeśli to nie słowo kluczowe, to musi być identyfikator.
            # Specyfikacja pkt 10 mówi: [_a-z]+.
            # Jeśli user wpisał np. "Zmienna", to tutaj wpadnie jako PIDENTIFIER.
            # Możemy tu rzucić błąd, jeśli chcemy być bardzo restrykcyjni,
            # ale często lepiej pozwolić parserowi działać.
            pass

        return t

    # --- Obsługa nowych linii ---
    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += len(t.value)

    # --- Obsługa błędów ---
    def error(self, t):
        print(
            f"Błąd leksykalny: Nieznany znak '{t.value[0]}' w linii {self.lineno}")
        self.index += 1


if __name__ == '__main__':
    data = """
    PROCEDURE test(T a, b) IS
        x, y[10:20]
    IN
        x := 10;
        y[15] := x + 5; # Komentarz
        WRITE x;
    END
    """
    lexer = KompilatorLexer()
    for tok in lexer.tokenize(data):
        print(f'type={tok.type}, value={tok.value}, lineno={tok.lineno}')
