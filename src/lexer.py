from sly import Lexer


class KompilatorLexer(Lexer):
    tokens = {
        # Słowa kluczowe
        "PROCEDURE", "PROGRAM", "IS", "IN", "END",
        "IF", "THEN", "ELSE", "ENDIF",
        "WHILE", "DO", "ENDWHILE",
        "REPEAT", "UNTIL",
        "FOR", "FROM", "TO", "DOWNTO", "ENDFOR",
        "READ", "WRITE",

        # Typy argumentów
        "T", "I", "O",

        "PIDENTIFIER", "NUM",

        "PLUS", "MINUS", "TIMES", "DIV", "MOD",
        "ASSIGN", "EQ", "NEQ", "LE", "GE", "LT", "GT",
        "LPAREN", "RPAREN", "LBRACKET", "RBRACKET", "COLON", "SEMICOLON", "COMMA"
    }

    ignore = ' \t'
    ignore_comment = r'\#.*'

    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += len(t.value)

    # Operatory
    ASSIGN = r':='
    NEQ = r'!='
    GE = r'>='
    LE = r'<='
    EQ = r'='
    LT = r'<'
    GT = r'>'

    PLUS = r'\+'
    MINUS = r'-'
    TIMES = r'\*'
    DIV = r'/'
    MOD = r'%'

    LPAREN = r'\('
    RPAREN = r'\)'
    LBRACKET = r'\['
    RBRACKET = r'\]'
    COLON = r':'
    SEMICOLON = r';'
    COMMA = r','

    # Liczby
    @_(r'\d+')
    def NUM(self, t):
        t.value = int(t.value)
        return t

    # Identyfikatory i Słowa Kluczowe
    # Regex łapie słowa zaczynające się od litery (dużej lub małej)
    @_(r'[a-zA-Z_][a-zA-Z0-9_]*')
    def PIDENTIFIER(self, t):
        # Mapa słów kluczowych - klucze muszą być dokładnie takie jak w kodzie źródłowym
        reserved = {
            'PROCEDURE': 'PROCEDURE', 'PROGRAM': 'PROGRAM', 'IS': 'IS', 'IN': 'IN', 'END': 'END',
            'IF': 'IF', 'THEN': 'THEN', 'ELSE': 'ELSE', 'ENDIF': 'ENDIF',
            'WHILE': 'WHILE', 'DO': 'DO', 'ENDWHILE': 'ENDWHILE',
            'REPEAT': 'REPEAT', 'UNTIL': 'UNTIL',
            'FOR': 'FOR', 'FROM': 'FROM', 'TO': 'TO', 'DOWNTO': 'DOWNTO', 'ENDFOR': 'ENDFOR',
            'READ': 'READ', 'WRITE': 'WRITE',
            # Typy zmiennych (Duże litery)
            'T': 'T', 'I': 'I', 'O': 'O'
        }

        # Sprawdzamy dokładnie to, co przyszło (bez upper())
        # Dzięki temu 'i' (zmienna) != 'I' (typ)
        token_type = reserved.get(t.value)
        if token_type:
            t.type = token_type

        return t

    def error(self, t):
        print(
            f"Błąd leksykalny: Nieznany znak '{t.value[0]}' w linii {self.lineno}")
        self.index += 1
