# Domyślny cel
all: install vm-build
	@echo "Tworzenie skryptu uruchomieniowego 'kompilator'..."
	@echo '#!/usr/bin/env python3' > kompilator
	@echo 'import sys' >> kompilator
	@echo 'import os' >> kompilator
	@echo '# Dodajemy katalog src do ścieżki wyszukiwania modułów' >> kompilator
	@echo 'sys.path.append(os.path.join(os.getcwd(), "src"))' >> kompilator
	@echo 'from main import main' >> kompilator
	@echo 'if __name__ == "__main__":' >> kompilator
	@echo '    main()' >> kompilator
	@chmod +x kompilator
	@echo "Gotowe. Użycie: ./kompilator <input> <output>"

# Budowanie maszyny wirtualnej (wywołuje make w katalogu vm)
vm-build:
	$(MAKE) -C vm

# Instalacja zależności
install:
	sudo python3 -m pip install -r requirements.txt

# Sprzątanie
clean:
	rm -rf src/__pycache__
	rm -f kompilator
	rm -f parser.out parsetab.py
	$(MAKE) -C vm clean

test:
	python3 -m unittest discover src/tests