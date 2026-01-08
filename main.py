import sys

def main():
    # Zgodnie z  wywołanie to: kompilator <input> <output>
    if len(sys.argv) != 3:
        print("Użycie: kompilator <plik_wejściowy> <plik_wyjściowy>")
        return

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    print(f"Kompilacja pliku: {input_file} -> {output_file}")
    # Tutaj wstawisz wywołanie parsera i generatora kodu

if __name__ == "__main__":
    main()