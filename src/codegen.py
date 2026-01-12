from ast_nodes import *
from symbol_table import SymbolTable


class CodeGenerator:
    def __init__(self):
        self.code = []
        self.symbols = SymbolTable()
        self.symbols.memory_offset = 0
        self.k = 0
        self.labels_map = {}
        self.k_counter = 0
        self.procedures_map = {}
        self.procedures_args = {}

    def emit(self, instruction):
        self.code.append(instruction)
        self.k += 1

    def get_addr(self, name):
        symbol = self.symbols.get(name)
        return symbol.address

    def new_label(self):
        self.k_counter += 1
        return f"__L{self.k_counter}__"

    def mark_label(self, label):
        self.labels_map[label] = self.k

    def resolve_labels(self):
        resolved_code = []
        for line in self.code:
            parts = line.split()
            if len(parts) > 1 and parts[1].startswith("__L"):
                label = parts[1]
                if label in self.labels_map:
                    target = self.labels_map[label]
                    resolved_code.append(f"{parts[0]} {target}")
                else:
                    raise Exception(
                        f"Błąd wewnętrzny: Nieznana etykieta {label}")
            else:
                resolved_code.append(line)
        self.code = resolved_code

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

    # --- POPRAWKA: Obsługa odczytu (Zwykła zmienna vs Parametr-Referencja) ---
    def load_value_to_reg(self, node, reg='a'):
        if isinstance(node, Variable):
            symbol = self.symbols.get(node.name)
            if symbol.is_param:
                # Parametr trzyma ADRES rzeczywistej zmiennej -> Dereferencja
                self.emit(f"LOAD {symbol.address}")  # Załaduj wskaźnik
                # Pobierz wartość spod wskaźnika
                self.emit("RLOAD a")
            else:
                # Zwykła zmienna lokalna/globalna
                self.emit(f"LOAD {symbol.address}")

        elif isinstance(node, Number):
            self.gen_number(node.value)
        else:
            self.generate(node)

        if reg != 'a':
            self.emit(f"SWP {reg}")

    def gen_array_addr(self, name, index_node):
        symbol = self.symbols.get(name)
        if isinstance(index_node, Number):
            self.gen_number(index_node.value)
            self.emit("SWP b")
        elif isinstance(index_node, Variable):
            # Tu używamy load_value_to_reg, żeby obsłużyć ewentualny indeks będący parametrem
            self.load_value_to_reg(index_node, 'a')
            self.emit("SWP b")
        else:
            self.generate(index_node)
            self.emit("SWP b")

        if symbol.is_param and symbol.is_array:
            self.emit(f"LOAD {symbol.address}")
            self.emit("ADD b")
            self.emit("SWP b")
        else:
            self.gen_number(symbol.array_start)
            self.emit("SWP b")
            self.emit("SUB b")
            self.emit("SWP b")
            self.gen_number(symbol.address)
            self.emit("ADD b")
            self.emit("SWP b")

    def generate(self, node):
        method_name = f'visit_{type(node).__name__}'
        return getattr(self, method_name, self.generic_visit)(node)

    def generic_visit(self, node):
        raise Exception(f"Nieznany węzeł AST: {type(node).__name__}")

    def visit_Program(self, node):
        main_label = self.new_label()
        self.emit(f"JUMP {main_label}")
        for proc in node.procedures:
            self.visit_Procedure(proc)
        self.mark_label(main_label)
        self.visit_Main(node.main)
        self.emit("HALT")
        self.resolve_labels()

    def visit_Main(self, node):
        self.symbols.enter_scope()
        for decl in node.declarations:
            if isinstance(decl, str):
                self.symbols.declare_variable(decl)
            elif isinstance(decl, ArrayDecl):
                self.symbols.declare_array(decl.name, decl.start, decl.end)
        for cmd in node.commands:
            self.generate(cmd)
        self.symbols.exit_scope()

    def visit_Procedure(self, node):
        start_label = self.new_label()
        self.procedures_map[node.name] = start_label
        self.mark_label(start_label)
        self.symbols.enter_scope()

        args_symbols = []
        for arg_type, arg_name in node.args:
            is_array = (arg_type == 'T')
            # Parametry skalarne (I, O) też są teraz "adresami" (referencjami)
            sym = self.symbols.declare_param(arg_name, is_array=is_array)
            args_symbols.append(sym)
        self.procedures_args[node.name] = args_symbols

        for decl in node.declarations:
            if isinstance(decl, str):
                self.symbols.declare_variable(decl)
            elif isinstance(decl, ArrayDecl):
                self.symbols.declare_array(decl.name, decl.start, decl.end)

        for cmd in node.commands:
            self.generate(cmd)
        self.symbols.exit_scope()
        self.emit("RTRN")

    # --- POPRAWKA: Przekazywanie adresów zamiast wartości ---
    def visit_ProcCall(self, node):
        if node.name not in self.procedures_args:
            raise Exception(f"Błąd: Nieznana procedura '{node.name}'")
        param_symbols = self.procedures_args[node.name]

        for param_sym, arg_val in zip(param_symbols, node.args):
            # Jeśli parametr jest tablicą:
            if param_sym.is_array:
                orig_sym = self.symbols.get(arg_val.name)
                self.gen_number(orig_sym.address)
                self.emit("SWP b")
                self.gen_number(orig_sym.array_start)
                self.emit("SWP b")
                self.emit("SUB b")
                self.emit(f"STORE {param_sym.address}")

            # Jeśli parametr jest zmienną skalarną (I/O):
            else:
                if isinstance(arg_val, Variable):
                    # Przekazujemy ADRES zmiennej, a nie jej wartość
                    orig_sym = self.symbols.get(arg_val.name)
                    self.gen_number(orig_sym.address)
                    self.emit(f"STORE {param_sym.address}")
                elif isinstance(arg_val, Number):
                    # Dla stałej musimy utworzyć tymczasową zmienną w pamięci i przekazać jej adres
                    val_addr = self.symbols.memory_offset
                    self.symbols.memory_offset += 1
                    self.gen_number(arg_val.value)
                    # Zapisz wartość pod tymczasowym adresem
                    self.emit(f"STORE {val_addr}")

                    self.gen_number(val_addr)      # Załaduj ten adres
                    # Przekaż adres do parametru
                    self.emit(f"STORE {param_sym.address}")
                else:
                    raise Exception(
                        "Argument wywołania musi być zmienną lub liczbą")

        target_label = self.procedures_map[node.name]
        self.emit(f"CALL {target_label}")

    def visit_For(self, node):
        try:
            iter_symbol = self.symbols.get(node.iterator)
        except:
            iter_symbol = self.symbols.declare_variable(node.iterator)
            iter_symbol.is_iterator = True
        iter_addr = iter_symbol.address

        self.generate(node.start_expr)
        self.emit(f"STORE {iter_addr}")
        self.generate(node.end_expr)

        # Alokacja limitu
        limit_addr = self.symbols.memory_offset
        self.symbols.memory_offset += 1
        self.emit(f"STORE {limit_addr}")

        start_label = self.new_label()
        end_label = self.new_label()
        self.mark_label(start_label)

        self.emit(f"LOAD {iter_addr}")
        self.emit("SWP c")
        self.emit(f"LOAD {limit_addr}")
        self.emit("SWP b")
        self.emit("SWP c")

        if node.downto:
            self.emit("SWP b")
            self.emit("SUB b")
            self.emit(f"JPOS {end_label}")
        else:
            self.emit("SUB b")
            self.emit(f"JPOS {end_label}")

        for cmd in node.commands:
            self.generate(cmd)

        self.emit(f"LOAD {iter_addr}")
        if node.downto:
            self.emit("DEC a")
        else:
            self.emit("INC a")
        self.emit(f"STORE {iter_addr}")
        self.emit(f"JUMP {start_label}")
        self.mark_label(end_label)
        # Nie zwalniamy pamięci (fix kolizji)

    # --- POPRAWKA: Zapis do zmiennej (obsługa zapisu przez wskaźnik) ---
    def visit_Assign(self, node):
        # 1. Oblicz wartość wyrażenia -> r_a
        self.generate(node.expression)

        symbol = self.symbols.get(node.identifier)
        if symbol.is_param:
            # Zapisz wartość w temp, załaduj adres, zapisz pośrednio
            temp = self.symbols.memory_offset
            self.symbols.memory_offset += 1
            self.emit(f"STORE {temp}")       # Zapisz wynik

            self.emit(f"LOAD {symbol.address}")  # r_a = Wskaźnik
            self.emit("SWP b")               # r_b = Wskaźnik

            self.emit(f"LOAD {temp}")        # r_a = Wynik
            self.emit("RSTORE b")            # *Wskaźnik = Wynik
        else:
            # Zwykły zapis
            self.emit(f"STORE {symbol.address}")
            symbol.is_initialized = True

    def visit_ArrayAssign(self, node):
        self.generate(node.expression)
        temp_addr = self.symbols.memory_offset
        self.symbols.memory_offset += 1
        self.emit(f"STORE {temp_addr}")
        self.gen_array_addr(node.name, node.index)
        self.emit(f"LOAD {temp_addr}")
        self.emit("RSTORE b")

    def visit_ArrayRef(self, node):
        self.gen_array_addr(node.name, node.index)
        self.emit("RLOAD b")

    def visit_Write(self, node):
        self.load_value_to_reg(node.value, 'a')
        self.emit("WRITE")

    # --- POPRAWKA: READ z obsługą wskaźników ---
    def visit_Read(self, node):
        self.emit("READ")
        symbol = self.symbols.get(node.identifier)

        if symbol.is_param:
            # READ wczytuje do r_a (kosztowne) lub nie?
            # Instrukcja READ: "Wczytuje wartość do rejestru p_0 (akumulatora)?"
            # Nie, specyfikacja maszyny mówi: "READ - wczytaj wartość do rejestru a (lub akumulatora)"?
            # Załóżmy standardowo że READ zostawia wartość w r_a (chociaż w VM kosztuje dużo)
            # Jeśli READ od razu zapisuje do pamięci... W VM 'READ' czyta do r_a (akumulatora).
            # Chwila, w Twoim poprzednim kodzie: self.emit("READ"); self.emit("STORE addr").
            # To sugeruje, że READ zostawia wartość w r_a.

            temp = self.symbols.memory_offset
            self.symbols.memory_offset += 1
            self.emit(f"STORE {temp}")          # Zapisz wczytaną wartość

            self.emit(f"LOAD {symbol.address}")  # Załaduj wskaźnik
            self.emit("SWP b")

            self.emit(f"LOAD {temp}")           # Przywróć wartość
            self.emit("RSTORE b")               # Zapisz pod wskaźnik
        else:
            self.emit(f"STORE {symbol.address}")
            symbol.is_initialized = True

    def visit_While(self, node):
        start_label = self.new_label()
        end_label = self.new_label()
        self.mark_label(start_label)
        self.gen_condition_jump(node.condition, end_label, jump_if_true=False)
        for cmd in node.commands:
            self.generate(cmd)
        self.emit(f"JUMP {start_label}")
        self.mark_label(end_label)

    def visit_Repeat(self, node):
        start_label = self.new_label()
        self.mark_label(start_label)
        for cmd in node.commands:
            self.generate(cmd)
        self.gen_condition_jump(
            node.condition, start_label, jump_if_true=False)

    def visit_If(self, node):
        else_label = self.new_label()
        end_label = self.new_label()
        self.gen_condition_jump(node.condition, else_label, jump_if_true=False)
        for cmd in node.commands_then:
            self.generate(cmd)
        self.emit(f"JUMP {end_label}")
        self.mark_label(else_label)
        if node.commands_else:
            for cmd in node.commands_else:
                self.generate(cmd)
        self.mark_label(end_label)

    def gen_condition_jump(self, condition, target_label, jump_if_true=False):
        self.load_value_to_reg(condition.right, 'a')
        is_simple = isinstance(condition.left, (Number, Variable))
        if is_simple:
            self.emit("SWP b")
            self.load_value_to_reg(condition.left, 'a')
        else:
            temp = self.symbols.memory_offset
            self.symbols.memory_offset += 1
            self.emit(f"STORE {temp}")
            self.generate(condition.left)
            self.emit("SWP c")
            self.emit(f"LOAD {temp}")
            self.emit("SWP b")
            self.emit("SWP c")
            # Nie zwalniamy pamięci

        op = condition.op
        def sub_ab(): self.emit("SUB b")
        def sub_ba(): self.emit("SWP b"); self.emit("SUB b")

        if op == '>':
            sub_ab()
            self.emit(
                f"JPOS {target_label}" if jump_if_true else f"JZERO {target_label}")
        elif op == '<':
            sub_ba()
            self.emit(
                f"JPOS {target_label}" if jump_if_true else f"JZERO {target_label}")
        elif op == '>=':
            sub_ba()
            self.emit(
                f"JZERO {target_label}" if jump_if_true else f"JPOS {target_label}")
        elif op == '<=':
            sub_ab()
            self.emit(
                f"JZERO {target_label}" if jump_if_true else f"JPOS {target_label}")
        elif op == '=':
            if jump_if_true:
                fail = self.new_label()
                sub_ab()
                self.emit(f"JPOS {fail}")
                sub_ba()
                self.emit(f"JPOS {fail}")
                self.emit(f"JUMP {target_label}")
                self.mark_label(fail)
            else:
                sub_ab()
                self.emit(f"JPOS {target_label}")
                sub_ba()
                self.emit(f"JPOS {target_label}")
        elif op == '!=':
            if jump_if_true:
                sub_ab()
                self.emit(f"JPOS {target_label}")
                sub_ba()
                self.emit(f"JPOS {target_label}")
            else:
                fail = self.new_label()
                sub_ab()
                self.emit(f"JPOS {fail}")
                sub_ba()
                self.emit(f"JPOS {fail}")
                self.emit(f"JUMP {target_label}")
                self.mark_label(fail)

    def visit_BinOp(self, node):
        if node.op == '*' and isinstance(node.right, Number) and node.right.value == 2:
            self.generate(node.left)
            self.emit("SHL a")
            return
        if node.op == '*' and isinstance(node.left, Number) and node.left.value == 2:
            self.generate(node.right)
            self.emit("SHL a")
            return
        if node.op == '/' and isinstance(node.right, Number) and node.right.value == 2:
            self.generate(node.left)
            self.emit("SHR a")
            return
        if node.op == '%' and isinstance(node.right, Number) and node.right.value == 2:
            self.generate(node.left)
            self.emit("SWP b")
            self.emit("SWP b")
            self.emit("SHR a")
            self.emit("SHL a")
            self.emit("SWP b")
            self.emit("SUB b")
            return

        self.generate(node.right)
        rhs_addr = self.symbols.memory_offset
        self.symbols.memory_offset += 1
        self.emit(f"STORE {rhs_addr}")
        self.generate(node.left)
        if node.op == '+':
            self.emit(f"ADD {rhs_addr}")
        elif node.op == '-':
            self.emit(f"SUB {rhs_addr}")
        elif node.op in ['*', '/', '%']:
            lhs_addr = self.symbols.memory_offset
            self.symbols.memory_offset += 1
            self.emit(f"STORE {lhs_addr}")
            if node.op == '*':
                self.gen_mul_optimized(lhs_addr, rhs_addr)
            elif node.op == '/':
                self.gen_div_mod(lhs_addr, rhs_addr, False)
            elif node.op == '%':
                self.gen_div_mod(lhs_addr, rhs_addr, True)

    def visit_Number(self, node): self.gen_number(node.value)

    def visit_Variable(self, node): self.load_value_to_reg(
        node, 'a')  # Używamy load_value_to_reg!

    def gen_mul_optimized(self, val_a_addr, val_b_addr):
        res_addr = self.symbols.memory_offset
        self.symbols.memory_offset += 1
        self.emit("RST a")
        self.emit(f"STORE {res_addr}")
        self.emit(f"LOAD {val_a_addr}")
        self.emit("SWP c")
        self.emit(f"LOAD {val_b_addr}")
        self.emit("SWP b")
        loop_start = self.new_label()
        loop_end = self.new_label()
        self.mark_label(loop_start)
        self.emit("RST a")
        self.emit("ADD b")
        self.emit(f"JZERO {loop_end}")
        self.emit("RST a")
        self.emit("ADD b")
        self.emit("SHR a")
        self.emit("SHL a")
        self.emit("SWP d")
        self.emit("RST a")
        self.emit("ADD b")
        self.emit("SUB d")
        skip = self.new_label()
        self.emit(f"JZERO {skip}")
        self.emit(f"LOAD {res_addr}")
        self.emit("ADD c")
        self.emit(f"STORE {res_addr}")
        self.mark_label(skip)
        self.emit("RST a")
        self.emit("ADD c")
        self.emit("SHL a")
        self.emit("SWP c")
        self.emit("RST a")
        self.emit("ADD b")
        self.emit("SHR a")
        self.emit("SWP b")
        self.emit(f"JUMP {loop_start}")
        self.mark_label(loop_end)
        self.emit(f"LOAD {res_addr}")

    def gen_div_mod(self, addr_a, addr_b, want_mod=False):
        end = self.new_label()
        self.emit(f"LOAD {addr_b}")
        self.emit(f"JZERO {end}")
        rem = self.symbols.memory_offset
        self.symbols.memory_offset += 1
        quot = self.symbols.memory_offset
        self.symbols.memory_offset += 1
        div = self.symbols.memory_offset
        self.symbols.memory_offset += 1
        mult = self.symbols.memory_offset
        self.symbols.memory_offset += 1
        self.emit(f"LOAD {addr_a}")
        self.emit(f"STORE {rem}")
        self.emit("RST a")
        self.emit(f"STORE {quot}")
        self.emit(f"LOAD {addr_b}")
        self.emit(f"STORE {div}")
        self.emit("RST a")
        self.emit("INC a")
        self.emit(f"STORE {mult}")
        l_scale = self.new_label()
        l_scale_end = self.new_label()
        self.mark_label(l_scale)
        self.emit(f"LOAD {rem}")
        self.emit("SWP b")
        self.emit(f"LOAD {div}")
        self.emit("SUB b")
        self.emit(f"JPOS {l_scale_end}")
        self.emit(f"LOAD {div}")
        self.emit("SHL a")
        self.emit(f"STORE {div}")
        self.emit(f"LOAD {mult}")
        self.emit("SHL a")
        self.emit(f"STORE {mult}")
        self.emit(f"JUMP {l_scale}")
        self.mark_label(l_scale_end)
        l_sub = self.new_label()
        l_sub_end = self.new_label()
        self.mark_label(l_sub)
        self.emit(f"LOAD {mult}")
        self.emit(f"JZERO {l_sub_end}")
        self.emit(f"LOAD {rem}")
        self.emit("SWP b")
        self.emit(f"LOAD {div}")
        self.emit("SUB b")
        skip = self.new_label()
        self.emit(f"JPOS {skip}")
        self.emit(f"LOAD {rem}")
        self.emit("SWP b")
        self.emit(f"LOAD {div}")
        self.emit("SWP c")
        self.emit("SWP b")
        self.emit("SUB c")
        self.emit(f"STORE {rem}")
        self.emit(f"LOAD {quot}")
        self.emit("SWP b")
        self.emit(f"LOAD {mult}")
        self.emit("ADD b")
        self.emit(f"STORE {quot}")
        self.mark_label(skip)
        self.emit(f"LOAD {div}")
        self.emit("SHR a")
        self.emit(f"STORE {div}")
        self.emit(f"LOAD {mult}")
        self.emit("SHR a")
        self.emit(f"STORE {mult}")
        self.emit(f"JUMP {l_sub}")
        self.mark_label(l_sub_end)
        if want_mod:
            self.emit(f"LOAD {rem}")
        else:
            self.emit(f"LOAD {quot}")
        self.mark_label(end)
