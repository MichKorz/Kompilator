class Symbol:
    def __init__(self, name, address, is_array=False, array_start=0, array_end=0, is_iterator=False):
        self.name = name
        self.address = address       # Fizyczny adres w pamięci VM (p_i)
        self.is_array = is_array
        # Indeks początkowy (dla tab[10:20] -> 10)
        self.array_start = array_start
        self.array_end = array_end     # Indeks końcowy
        # Czy jest to iterator pętli FOR (read-only)
        self.is_iterator = is_iterator
        self.is_initialized = False    # Czy zmienna ma nadaną wartość

    def __repr__(self):
        type_s = f"Array[{self.array_start}:{self.array_end}]" if self.is_array else "Var"
        iter_s = " (Iterator)" if self.is_iterator else ""
        return f"<{self.name}: {type_s} @ {self.address}{iter_s}>"


class SymbolTable:
    def __init__(self):
        # Stos zakresów. Każdy element to słownik {nazwa: Symbol}
        # Na początku mamy zakres globalny (choć w tym języku zmienne są w Main lub Procedurach)
        self.scopes = [{}]

        # Licznik wolnych komórek pamięci w maszynie wirtualnej
        # Zaczynamy od 0, ale rejestry r_a..r_h są osobne, więc p_0 jest bezpieczne.
        self.memory_offset = 0

    def enter_scope(self):
        """Wchodzi do nowego zakresu (np. początek procedury)"""
        self.scopes.append({})

    def exit_scope(self):
        """Wychodzi z zakresu (koniec procedury)"""
        self.scopes.pop()

    def get(self, name):
        """
        Szuka symbolu. Zgodnie z, w procedurze widzimy tylko zmienne lokalne/parametry.
        Dlatego szukamy TYLKO w obecnym zakresie (self.scopes[-1]).
        """
        current_scope = self.scopes[-1]
        if name in current_scope:
            return current_scope[name]

        raise Exception(f"Błąd: Niezadeklarowana zmienna '{name}'")

    def declare_variable(self, name, is_iterator=False):
        """Deklaruje zwykłą zmienną"""
        current_scope = self.scopes[-1]

        if name in current_scope:
            raise Exception(
                f"Błąd: Druga deklaracja zmiennej '{name}'")  # [cite: 4]

        # Przydziel adres w pamięci
        address = self.memory_offset
        self.memory_offset += 1

        symbol = Symbol(name, address, is_iterator=is_iterator)
        current_scope[name] = symbol
        return symbol

    def declare_array(self, name, start, end):
        """Deklaruje tablicę tab[start:end]"""
        current_scope = self.scopes[-1]

        if name in current_scope:
            raise Exception(f"Błąd: Druga deklaracja zmiennej '{name}'")

        # Walidacja zakresu tablicy
        if start > end:
            raise Exception(
                f"Błąd: Niepoprawny zakres tablicy '{name}' ({start} > {end})")

        # Oblicz rozmiar tablicy
        size = end - start + 1

        # Przydziel blok pamięci
        base_address = self.memory_offset
        self.memory_offset += size

        symbol = Symbol(name, base_address, is_array=True,
                        array_start=start, array_end=end)
        current_scope[name] = symbol
        return symbol

    def get_iterator(self, name):
        """Pomocnicza funkcja do sprawdzania modyfikacji iteratora"""
        try:
            sym = self.get(name)
            return sym.is_iterator
        except:
            return False
