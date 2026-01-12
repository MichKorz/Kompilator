class Symbol:
    def __init__(self, name, address, is_array=False, array_start=0, array_end=0, is_iterator=False, is_param=False):
        self.name = name
        self.address = address       # Fizyczny adres w pamięci
        self.is_array = is_array
        self.array_start = array_start
        self.array_end = array_end
        self.is_iterator = is_iterator
        self.is_param = is_param     # Czy zmienna jest parametrem procedury
        self.is_initialized = False

    def __repr__(self):
        type_s = "Param" if self.is_param else (
            "Array" if self.is_array else "Var")
        return f"<{self.name}: {type_s} @ {self.address}>"


class SymbolTable:
    def __init__(self):
        # Stos zakresów. Każdy element to słownik {nazwa: Symbol}
        # scope[0] to zmienne globalne (Main), scope[1+] to zmienne lokalne procedur
        self.scopes = [{}]
        self.memory_offset = 0

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        self.scopes.pop()

    def get(self, name):
        # Szukaj od najnowszego zakresu (lokalnego) w górę
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise Exception(f"Błąd: Niezadeklarowana zmienna '{name}'")

    def declare_variable(self, name):
        current_scope = self.scopes[-1]
        if name in current_scope:
            raise Exception(f"Błąd: Druga deklaracja zmiennej '{name}'")

        address = self.memory_offset
        self.memory_offset += 1

        symbol = Symbol(name, address)
        current_scope[name] = symbol
        return symbol

    def declare_array(self, name, start, end):
        current_scope = self.scopes[-1]
        if name in current_scope:
            raise Exception(f"Błąd: Druga deklaracja zmiennej '{name}'")

        size = end - start + 1
        address = self.memory_offset
        self.memory_offset += size

        symbol = Symbol(name, address, is_array=True,
                        array_start=start, array_end=end)
        current_scope[name] = symbol
        return symbol

    def declare_param(self, name, is_array=False):
        """Deklaruje parametr procedury (zawsze pojedyncza komórka pamięci).
        Jeśli is_array=True, zmienna przechowuje wirtualny adres bazowy tablicy."""
        current_scope = self.scopes[-1]
        if name in current_scope:
            raise Exception(f"Błąd: Duplikat parametru '{name}'")

        address = self.memory_offset
        self.memory_offset += 1

        symbol = Symbol(name, address, is_array=is_array, is_param=True)
        current_scope[name] = symbol
        return symbol
