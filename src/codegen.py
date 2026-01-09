# codegen.py
from ast_nodes import *


class CodeGenerator:
    def __init__(self):
        self.code = []       # Lista instrukcji asemblera
        self.memory = {}     # Mapa: zmienna -> adres w pamięci
        self.mem_offset = 0  # Następny wolny adres pamięci

    def emit(self, instruction):
        """Dodaje instrukcję do listy"""
        self.code.append(instruction)

    def get_var_addr(self, name):
        """Zwraca adres zmiennej. Rzuca błąd, jeśli nieznana."""
        if name not in self.memory:
            raise Exception(f"Błąd: Niezadeklarowana zmienna '{name}'")
        return self.memory[name]

    # --- Generowanie stałych (Specyfika maszyny) ---
    def gen_number(self, value):
        """
        Generuje kod, który tworzy liczbę `value` w rejestrze r_a.
        Używa: RST (zero), SHL (bitshift), INC (dodaj 1).
        """
        self.emit("RST a")  # a = 0
        if value == 0:
            return

        # Algorytm: idziemy po bitach liczby od najstarszego (pomijając pierwszy 0)
        binary = bin(value)[2:]  # np. 5 -> "101"

        # Pierwszy bit (zawsze 1 dla value > 0)
        self.emit("INC a")

        # Reszta bitów
        for bit in binary[1:]:
            self.emit("SHL a")  # Przesuń w lewo (mnożenie * 2)
            if bit == '1':
                self.emit("INC a")  # Dodaj 1 jeśli bit to 1

    # --- Odwiedzanie węzłów AST ---

    def generate(self, node):
        """Główna funkcja dispatchera"""
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception(
            f"Nie zaimplementowano generatora dla: {type(node).__name__}")

    def visit_Program(self, node):
        # 1. Przydział pamięci dla zmiennych w MAIN
        # (W pełnej wersji tu będzie też obsługa procedur)
        self.visit_Main(node.main)
        self.emit("HALT")  # Koniec programu

    def visit_Main(self, node):
        # Rejestracja zmiennych w pamięci
        for var_name in node.declarations:
            if var_name in self.memory:
                raise Exception(f"Duplikat deklaracji: {var_name}")
            self.memory[var_name] = self.mem_offset
            self.mem_offset += 1

        # Generowanie kodu dla komend
        for cmd in node.commands:
            self.generate(cmd)

    def visit_Assign(self, node):
        # 1. Oblicz wyrażenie (wynik wyląduje w r_a)
        self.generate(node.expression)

        # 2. Zapisz wynik pod adresem zmiennej
        addr = self.get_var_addr(node.identifier)
        self.emit(f"STORE {addr}")

    def visit_Write(self, node):
        # Specyfikacja mówi: WRITE value. Value może być liczbą lub zmienną.
        # Musimy załadować to do r_a
        if isinstance(node.value, Number):
            self.gen_number(node.value.value)
        elif isinstance(node.value, Variable):
            addr = self.get_var_addr(node.value.name)
            self.emit(f"LOAD {addr}")
        else:
            raise Exception("WRITE obsługuje tylko zmienne i liczby")

        self.emit("WRITE")

    def visit_Number(self, node):
        # Wygeneruj liczbę w r_a
        self.gen_number(node.value)

    def visit_Variable(self, node):
        # Załaduj zmienną z pamięci do r_a
        addr = self.get_var_addr(node.name)
        self.emit(f"LOAD {addr}")

    def visit_BinOp(self, node):
        if node.op == '+':
            # Strategia a + b:
            # 1. Wylicz prawą stronę ('b') -> wynik w r_a
            self.generate(node.right)

            # 2. Przenieś wynik do r_b (pomocniczy), żeby zwolnić r_a
            self.emit("SWP b")

            # 3. Wylicz lewą stronę ('a') -> wynik w r_a
            self.generate(node.left)

            # 4. Dodaj r_b do r_a
            self.emit("ADD b")

        # Tutaj dodamy odejmowanie, mnożenie itp. później
