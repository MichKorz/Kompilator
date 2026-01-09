import sys
from lexer import KompilatorLexer
from parser import KompilatorParser
from codegen import CodeGenerator


def main():
    if len(sys.argv) != 3:
        print("Użycie: kompilator <plik_wejściowy> <plik_wyjściowy>")
        return

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    # Wczytaj plik
    try:
        with open(input_file, 'r') as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Błąd: Nie znaleziono pliku {input_file}")
        return

    # 1. Lexer
    lexer = KompilatorLexer()

    # 2. Parser
    parser = KompilatorParser()
    try:
        ast = parser.parse(lexer.tokenize(text))
    except Exception as e:
        print(f"Błąd parsowania: {e}")
        return

    if not ast:
        print("Błąd: Parser nie zwrócił drzewa AST (pusty plik lub błąd składni).")
        return

    # 3. Code Generation
    generator = CodeGenerator()
    try:
        generator.generate(ast)
    except Exception as e:
        print(f"Błąd kompilacji: {e}")
        return

    # Zapisz wynik
    with open(output_file, 'w') as f:
        for line in generator.code:
            f.write(line + '\n')

    print(f"Kompilacja zakończona sukcesem! Wynik w {output_file}")


if __name__ == "__main__":
    main()
