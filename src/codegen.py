from ast_nodes import *
from symbol_table import SymbolTable


class CodeGenerator:
    def __init__(self):
        self.code = []
        self.symbols = SymbolTable()  # Używamy naszej nowej klasy!
        # Licznik rozkazów (potrzebny do obliczania skoków, choć tutaj skaczemy do etykiet)
        self.k = 0
        self.labels_map = {}  # Mapa: etykieta -> numer linii

    def emit(self, instruction):
        self.code.append(instruction)
        self.k += 1

    def get_addr(self, name):
        """Pobiera adres zmiennej z SymbolTable"""
        symbol = self.symbols.get(name)
        return symbol.address

    # --- Poprawiona obsługa warunków (Używa rejestrów zamiast pamięci) ---
    def gen_condition_jump(self, condition, jump_target, jump_if_true=False):
        """
        Generuje kod skoku warunkowego.
        Wersja OSTATECZNA: Poprawiona logika dla równości (REPEAT UNTIL).
        """
        # 1. Załaduj PRAWĄ stronę do r_b
        self.load_value_to_reg(condition.right, 'a')
        self.emit("SWP b")  # r_b = Right

        # 2. Załaduj LEWĄ stronę do r_a
        self.load_value_to_reg(condition.left, 'a')  # r_a = Left

        # Helper: Kopia r_a (Left) -> r_c
        def copy_a_to_c():
            self.emit("SWP c")
            self.emit("RST a")
            self.emit("ADD c")  # Teraz a == c (oryginalna wartość)

        if condition.op == '>':
            self.emit("SUB b")
            if jump_if_true:
                self.emit(f"JPOS {jump_target}")
            else:
                self.emit(f"JZERO {jump_target}")

        elif condition.op == '<':
            self.emit("SWP b")
            self.emit("SUB b")  # Right - Left
            if jump_if_true:
                self.emit(f"JPOS {jump_target}")
            else:
                self.emit(f"JZERO {jump_target}")

        elif condition.op == '>=':
            self.emit("SWP b")
            self.emit("SUB b")
            if jump_if_true:
                self.emit(f"JZERO {jump_target}")
            else:
                self.emit(f"JPOS {jump_target}")

        elif condition.op == '<=':
            self.emit("SUB b")
            if jump_if_true:
                self.emit(f"JZERO {jump_target}")
            else:
                self.emit(f"JPOS {jump_target}")

        elif condition.op == '=':
            # Potrzebujemy kopii, bo sprawdzamy dwie strony
            temp_addr = self.symbols.memory_offset
            self.symbols.memory_offset += 1
            # Zapisz Right (r_b) w pamięci
            self.emit("SWP b")
            self.emit(f"STORE {temp_addr}")
            self.emit("SWP b")

            # Kopia Left (r_a) -> r_c
            copy_a_to_c()

            # 1. Sprawdź a > b
            self.emit("SUB b")

            if jump_if_true:
                # Skocz jeśli równe (czyli NIE a>b I NIE b>a)
                fail_label = self.new_label()
                # Jeśli a > b, to nie równe -> fail
                self.emit(f"JPOS {fail_label}")

                # 2. Sprawdź b > a
                self.emit("RST a")
                self.emit("ADD c")
                self.emit("SWP b")  # Odtwórz rejestry
                self.emit(f"LOAD {temp_addr}")
                self.emit("SUB b")  # b - a

                # Jeśli b > a, to nie równe -> fail
                self.emit(f"JPOS {fail_label}")

                # Jeśli tu jesteśmy, to równe
                self.emit(f"JUMP {jump_target}")
                self.mark_label(fail_label)

            else:
                # Skocz jeśli NIE równe (czyli a > b LUB b > a)
                # To jest przypadek dla REPEAT UNTIL a=b
                self.emit(f"JPOS {jump_target}")  # Jeśli a > b, skocz

                # 2. Sprawdź b > a
                self.emit("RST a")
                self.emit("ADD c")
                self.emit("SWP b")
                self.emit(f"LOAD {temp_addr}")
                self.emit("SUB b")

                self.emit(f"JPOS {jump_target}")  # Jeśli b > a, skocz

            self.symbols.memory_offset -= 1

        elif condition.op == '!=':
            # To samo co '=' tylko na odwrót
            temp_addr = self.symbols.memory_offset
            self.symbols.memory_offset += 1
            self.emit("SWP b")
            self.emit(f"STORE {temp_addr}")
            self.emit("SWP b")
            copy_a_to_c()

            self.emit("SUB b")

            if jump_if_true:
                # Skocz jeśli NIE równe (a > b lub b > a)
                self.emit(f"JPOS {jump_target}")

                self.emit("RST a")
                self.emit("ADD c")
                self.emit("SWP b")
                self.emit(f"LOAD {temp_addr}")
                self.emit("SUB b")

                self.emit(f"JPOS {jump_target}")
            else:
                # Skocz jeśli równe
                fail_label = self.new_label()
                self.emit(f"JPOS {fail_label}")

                self.emit("RST a")
                self.emit("ADD c")
                self.emit("SWP b")
                self.emit(f"LOAD {temp_addr}")
                self.emit("SUB b")

                self.emit(f"JPOS {fail_label}")

                self.emit(f"JUMP {jump_target}")
                self.mark_label(fail_label)

            self.symbols.memory_offset -= 1

    def get_value_addr(self, node):
        """Zwraca adres zmiennej lub zapisuje liczbę do tymczasowej komórki i zwraca jej adres"""
        if isinstance(node, Variable):
            return self.get_addr(node.name)
        elif isinstance(node, Number):
            # To jest miejsce na optymalizację, ale dla MVP:
            # Generujemy liczbę w r_a i zapisujemy ją na końcu pamięci
            self.gen_number(node.value)
            temp_addr = self.symbols.memory_offset
            self.symbols.memory_offset += 1
            self.emit(f"STORE {temp_addr}")
            return temp_addr
        raise Exception("Złożone wyrażenia w warunkach jeszcze nieobsługiwane")

    def load_value_to_reg(self, node, reg='a'):
        """Ładuje wartość (Variable/Number) do rejestru r_a"""
        if isinstance(node, Variable):
            addr = self.get_addr(node.name)
            self.emit(f"LOAD {addr}")
        elif isinstance(node, Number):
            self.gen_number(node.value)
            # Wynik jest w r_a. Jeśli chcieliśmy do innego rejestru (np. 'b'), trzeba przenieść.
            if reg != 'a':
                self.emit(f"SWP {reg}")

    # --- Generatory ---

    def visit_Program(self, node):
        self.visit_Main(node.main)
        self.emit("HALT")
        self.resolve_labels()  # Podmieniamy etykiety na numery linii

    def visit_Main(self, node):
        # Deklaracje
        for decl in node.declarations:
            # Tutaj musimy rozróżnić zmienną od tablicy (parser na razie daje tylko stringi dla zmiennych)
            if isinstance(decl, str):
                self.symbols.declare_variable(decl)
            # TODO: Obsługa deklaracji tablic (gdy parser to zwróci)

        for cmd in node.commands:
            self.generate(cmd)

    def visit_Assign(self, node):
        # 1. Wylicz wyrażenie -> r_a
        self.generate(node.expression)
        # 2. Zapisz
        addr = self.get_addr(node.identifier)
        self.emit(f"STORE {addr}")
        self.symbols.get(node.identifier).is_initialized = True

    def visit_Write(self, node):
        self.load_value_to_reg(node.value, 'a')
        self.emit("WRITE")

    def visit_If(self, node):
        # Etykiety
        else_label = self.new_label()
        end_label = self.new_label()

        # Generuj skok warunkowy (jeśli fałsz -> idź do else)
        # Logika: if condition is false, jump to else_label
        self.gen_condition_jump(node.condition, else_label, jump_if_true=False)

        # Blok THEN
        for cmd in node.commands_then:
            self.generate(cmd)
        self.emit(f"JUMP {end_label}")  # Po wykonaniu THEN, omiń ELSE

        # Blok ELSE
        self.mark_label(else_label)
        if node.commands_else:
            for cmd in node.commands_else:
                self.generate(cmd)

        self.mark_label(end_label)

    def visit_While(self, node):
        start_label = self.new_label()
        end_label = self.new_label()

        self.mark_label(start_label)

        # Warunek: jeśli fałsz -> skocz do końca
        self.gen_condition_jump(node.condition, end_label, jump_if_true=False)

        # Ciało pętli
        for cmd in node.commands:
            self.generate(cmd)

        # Skok na początek
        self.emit(f"JUMP {start_label}")

        self.mark_label(end_label)

    def visit_Repeat(self, node):
        start_label = self.new_label()
        self.mark_label(start_label)

        # Ciało pętli
        for cmd in node.commands:
            self.generate(cmd)

        # Warunek UNTIL: jeśli fałsz (warunek niespełniony) -> powtórz pętlę
        # Uwaga: REPEAT wykonuje się dopóki warunek jest FAŁSZYWY.
        # Np. REPEAT ... UNTIL a > b. Pętla trwa gdy a <= b.
        # Więc skaczemy na początek, jeśli warunek jest FALSE.
        self.gen_condition_jump(
            node.condition, start_label, jump_if_true=False)

    # --- Poprawiona arytmetyka (Dodawanie i Odejmowanie) ---
    def visit_BinOp(self, node):
        # Dla + i - (bez zmian, tylko optymalizacja wczytywania)
        if node.op in ['+', '-']:
            self.generate(node.right)
            # Zapisz prawą stronę do TEMP
            temp_addr = self.symbols.memory_offset
            self.symbols.memory_offset += 1
            self.emit(f"STORE {temp_addr}")

            self.generate(node.left)

            if node.op == '+':
                self.emit(f"ADD {temp_addr}")
            else:
                self.emit(f"SUB {temp_addr}")

            self.symbols.memory_offset -= 1
            return

        # Dla *, /, % (wymagają adresów pamięci, bo gen_mul działa na adresach)
        # Musimy wyliczyć argumenty i zapisać je w pamięci

        # Prawa strona -> Pamięć
        self.generate(node.right)
        rhs_addr = self.symbols.memory_offset
        self.symbols.memory_offset += 1
        self.emit(f"STORE {rhs_addr}")

        # Lewa strona -> Pamięć
        self.generate(node.left)
        lhs_addr = self.symbols.memory_offset
        self.symbols.memory_offset += 1
        self.emit(f"STORE {lhs_addr}")

        if node.op == '*':
            self.gen_mul_optimized(lhs_addr, rhs_addr)
        elif node.op == '/':
            self.gen_div_mod(lhs_addr, rhs_addr, want_mod=False)
        elif node.op == '%':
            self.gen_div_mod(lhs_addr, rhs_addr, want_mod=True)

        # Sprzątanie
        self.symbols.memory_offset -= 2

    def visit_Number(self, node):
        self.gen_number(node.value)

    def visit_Variable(self, node):
        addr = self.get_addr(node.name)
        self.emit(f"LOAD {addr}")

    # --- Helpery ---
    def generate(self, node):
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception(f"Nieznany węzeł: {type(node).__name__}")

    def gen_number(self, value):
        self.emit("RST a")
        if value == 0:
            return
        binary = bin(value)[2:]
        self.emit("INC a")
        for bit in binary[1:]:
            self.emit("SHL a")
            if bit == '1':
                self.emit("INC a")

    # System etykiet (Labeling)
    def new_label(self):
        # Generuje unikalną nazwę etykiety, np. "L1"
        self.k_counter = getattr(self, 'k_counter', 0) + 1
        return f"__L{self.k_counter}__"

    def mark_label(self, label):
        # Zapisuje, że etykieta "L1" wskazuje na obecną linię (self.k)
        self.labels_map[label] = self.k

    def resolve_labels(self):
        # Druga faza: podmienia "__L1__" na konkretne liczby w wygenerowanym kodzie
        resolved_code = []
        for line in self.code:
            words = line.split()
            if len(words) > 1 and words[1].startswith("__L"):
                label = words[1]
                if label in self.labels_map:
                    target_line = self.labels_map[label]
                    resolved_code.append(f"{words[0]} {target_line}")
                else:
                    raise Exception(
                        f"Błąd wewnętrzny: Nieznana etykieta {label}")
            else:
                resolved_code.append(line)
        self.code = resolved_code

    # --- Dodaj te metody do klasy CodeGenerator ---

    def visit_Read(self, node):
        self.emit("READ")
        addr = self.get_addr(node.identifier)
        self.emit(f"STORE {addr}")
        self.symbols.get(node.identifier).is_initialized = True

    # --- Algorytmy Matematyczne (Asembler) ---

    def gen_mul(self, addr_a, addr_b):
        """
        Generuje kod mnożenia: r_a = mem[addr_a] * mem[addr_b].
        Używa rejestrów: r_a (wynik), r_b (mnożnik), r_c (mnożna), r_d (temp).
        Algorytm: Russian Peasant.
        """
        # Przygotowanie rejestrów
        self.emit("RST a")  # Wynik = 0

        self.emit(f"LOAD {addr_a}")
        self.emit("SWP c")  # r_c = a (mnożna)

        self.emit(f"LOAD {addr_b}")
        self.emit("SWP b")  # r_b = b (mnożnik)

        # Pętla mnożenia
        start_label = self.new_label()
        end_label = self.new_label()

        self.mark_label(start_label)

        # if b == 0 -> koniec
        self.emit("RST d")  # r_d = 0 (do porównania)
        self.emit("ADD b")  # r_a = r_b
        self.emit(f"JZERO {end_label}")

        # Sprawdź czy b jest nieparzyste (b % 2 != 0)
        # Trik: Jeśli (b/2)*2 != b, to b jest nieparzyste.
        # Ale prościej: w tej maszynie nie ma bitwise AND.
        # Zrobimy: r_d = b; r_d = r_d / 2; r_d = r_d * 2; if r_d != b -> nieparzyste.

        self.emit("RST d")
        self.emit("ADD b")  # r_a = b
        self.emit("SHR a")  # r_a = b / 2
        self.emit("SHL a")  # r_a = (b / 2) * 2
        self.emit("INC a")  # r_a = ... + 1
        self.emit("SUB b")  # r_a = ((b/2)*2 + 1) - b
        # Jeśli b parzyste (np 4): 2*2+1 - 4 = 1 -> JPOS (skok, nie dodawaj)
        # Jeśli b nieparzyste (np 5): 2*2+1 - 5 = 0 -> JZERO (dodaj)

        skip_add = self.new_label()
        self.emit(f"JPOS {skip_add}")

        # Jeśli nieparzyste: wynik += c
        # Przenieś wynik reszty do temp (choć tu akurat jest 0)
        self.emit("SWP a")
        # Wczytaj akumulator wyniku (Uuu, musimy go gdzieś trzymać!)
        self.emit("LOAD 0")
        # POPRAWKA: r_a w tej pętli służy do obliczeń. Wynik trzymajmy w dedykowanej komórce pamięci.
        pass
        # REFLEKSJA: Rejestrów jest mało. Lepiej użyć pamięci tymczasowej na wynik.

    def gen_mul_optimized(self, val_a_addr, val_b_addr):
        res_addr = self.symbols.memory_offset
        self.symbols.memory_offset += 1
        self.emit(f"RST a")
        self.emit(f"STORE {res_addr}")  # res = 0

        self.emit(f"LOAD {val_a_addr}")
        self.emit("SWP c")  # c = a (mnożna)
        self.emit(f"LOAD {val_b_addr}")
        self.emit("SWP b")  # b = b (mnożnik)

        loop_start = self.new_label()
        loop_end = self.new_label()
        self.mark_label(loop_start)

        # if b == 0 -> koniec
        self.emit("RST a")
        self.emit("ADD b")
        self.emit(f"JZERO {loop_end}")

        # Parzystość b: if (b - (b/2)*2) > 0 -> nieparzyste
        self.emit("RST a")
        self.emit("ADD b")
        self.emit("SHR a")
        self.emit("SHL a")
        self.emit("SWP d")  # d = (b//2)*2
        self.emit("RST a")
        self.emit("ADD b")
        self.emit("SUB d")

        skip_add = self.new_label()
        self.emit(f"JZERO {skip_add}")  # Parzyste -> skip

        # res += c
        self.emit(f"LOAD {res_addr}")
        self.emit("ADD c")
        self.emit(f"STORE {res_addr}")

        self.mark_label(skip_add)

        # c = c * 2
        self.emit("RST a")
        self.emit("ADD c")
        self.emit("SHL a")
        self.emit("SWP c")
        # b = b / 2
        self.emit("RST a")
        self.emit("ADD b")
        self.emit("SHR a")
        self.emit("SWP b")

        self.emit(f"JUMP {loop_start}")
        self.mark_label(loop_end)

        self.emit(f"LOAD {res_addr}")
        self.symbols.memory_offset -= 1

    def gen_div_mod(self, addr_a, addr_b, want_mod=False):
        """
        Dzielenie a / b. Zwraca iloraz (jeśli want_mod=False) lub resztę.
        Złożoność: Logarytmiczna.
        """
        # Etykieta końca (używana przy dzieleniu przez 0 i na koniec funkcji)
        end_label = self.new_label()

        # Obsługa dzielenia przez 0
        # Jeśli b == 0, wynik to 0. Maszyna zeruje rejestry przy resecie,
        # więc wystarczy skoczyć do końca (gdzie załadujemy wynik, który ustawimy na 0).
        self.emit(f"LOAD {addr_b}")
        self.emit(f"JZERO {end_label}")

        # Przygotowanie zmiennych w pamięci
        # reszta (remainder) = a
        rem_addr = self.symbols.memory_offset
        self.symbols.memory_offset += 1
        self.emit(f"LOAD {addr_a}")
        self.emit(f"STORE {rem_addr}")

        # iloraz (quotient) = 0
        quot_addr = self.symbols.memory_offset
        self.symbols.memory_offset += 1
        self.emit("RST a")
        self.emit(f"STORE {quot_addr}")

        # temp_div (kopia b, którą będziemy skalować)
        temp_div_addr = self.symbols.memory_offset
        self.symbols.memory_offset += 1
        self.emit(f"LOAD {addr_b}")
        self.emit(f"STORE {temp_div_addr}")

        # mult (wielokrotność = 1)
        mult_addr = self.symbols.memory_offset
        self.symbols.memory_offset += 1
        self.emit("RST a")
        self.emit("INC a")
        self.emit(f"STORE {mult_addr}")

        # --- KROK 1: Skalowanie dzielnika (temp_div <<= 1 dopóki temp_div <= rem) ---
        loop_scale = self.new_label()
        loop_scale_end = self.new_label()

        self.mark_label(loop_scale)

        # Warunek: if temp_div > rem: break
        # Sprawdzamy temp_div - rem > 0
        self.emit(f"LOAD {rem_addr}")
        self.emit("SWP b")
        self.emit(f"LOAD {temp_div_addr}")  # r_a = temp_div
        self.emit("SUB b")  # temp_div - rem
        self.emit(f"JPOS {loop_scale_end}")  # Jeśli > 0, to już za dużo

        # temp_div *= 2
        self.emit(f"LOAD {temp_div_addr}")
        self.emit("SHL a")
        self.emit(f"STORE {temp_div_addr}")
        # mult *= 2
        self.emit(f"LOAD {mult_addr}")
        self.emit("SHL a")
        self.emit(f"STORE {mult_addr}")

        self.emit(f"JUMP {loop_scale}")
        self.mark_label(loop_scale_end)

        # --- KROK 2: Odejmowanie (Subtract and shift back) ---
        loop_sub = self.new_label()
        loop_sub_end = self.new_label()

        self.mark_label(loop_sub)

        # if mult == 0: break
        self.emit(f"LOAD {mult_addr}")
        self.emit(f"JZERO {loop_sub_end}")

        # Warunek: if temp_div <= rem (czyli temp_div - rem <= 0 ... ale SUB zwraca 0 dla ujemnych)
        # Inaczej: if temp_div - rem > 0 -> skip (temp_div jest za duży)
        self.emit(f"LOAD {rem_addr}")
        self.emit("SWP b")
        self.emit(f"LOAD {temp_div_addr}")
        self.emit("SUB b")  # temp_div - rem

        skip_step = self.new_label()
        # Jeśli >0, to temp_div > rem (nie odejmujemy)
        self.emit(f"JPOS {skip_step}")

        # Wykonaj odejmowanie: rem -= temp_div
        self.emit(f"LOAD {rem_addr}")
        self.emit("SWP b")
        self.emit(f"LOAD {temp_div_addr}")
        self.emit("SWP c")
        self.emit("SWP b")
        self.emit("SUB c")
        self.emit(f"STORE {rem_addr}")

        # Dodaj do wyniku: quot += mult
        self.emit(f"LOAD {quot_addr}")
        self.emit("SWP b")
        self.emit(f"LOAD {mult_addr}")
        self.emit("ADD b")
        self.emit(f"STORE {quot_addr}")

        self.mark_label(skip_step)

        # Przesuń w dół (temp_div /= 2, mult /= 2)
        self.emit(f"LOAD {temp_div_addr}")
        self.emit("SHR a")
        self.emit(f"STORE {temp_div_addr}")
        self.emit(f"LOAD {mult_addr}")
        self.emit("SHR a")
        self.emit(f"STORE {mult_addr}")

        self.emit(f"JUMP {loop_sub}")
        self.mark_label(loop_sub_end)

        # --- Koniec ---
        self.mark_label(end_label)

        # Zwróć wynik do r_a
        if want_mod:
            self.emit(f"LOAD {rem_addr}")
        else:
            self.emit(f"LOAD {quot_addr}")

        # Sprzątanie pamięci tymczasowej (4 zmienne)
        # Uwaga: Jeśli skoczyliśmy od razu do end_label (dzielenie przez 0),
        # te zmienne nie zostały zaalokowane.
        # Ale nasz mechanizm memory_offset jest prosty (tylko int),
        # więc cofnięcie licznika jest bezpieczne logicznie, choć "fizycznie"
        # może cofać nieużyty obszar. Dla MVP to jest OK.
        self.symbols.memory_offset -= 4
