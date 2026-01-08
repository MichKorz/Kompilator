# Domyślny cel - przygotowanie "pliku wykonywalnego"
all: install
	@echo "Tworzenie skryptu uruchomieniowego 'kompilator'..."
	@echo '#!/usr/bin/env python3' > kompilator
	@echo 'import sys' >> kompilator
	@echo 'import os' >> kompilator
	@echo '# Ustawienie ścieżki, aby python widział moduły w bieżącym katalogu' >> kompilator
	@echo 'sys.path.append(os.getcwd())' >> kompilator
	@echo 'from main import main' >> kompilator
	@echo 'if __name__ == "__main__":' >> kompilator
	@echo '    main()' >> kompilator
	@chmod +x kompilator
	@echo "Gotowe. Użycie: ./kompilator <input> <output>"

# Instalacja zależności (to polecenie dla Ubuntu)
install:
	pip3 install -r requirements.txt

# Sprzątanie
clean:
	rm -rf __pycache__
	rm -f kompilator
	rm -f parser.out parsetab.py

# Testowanie (opcjonalnie, dla Ciebie)
test:
	python3 -m unittest discover tests