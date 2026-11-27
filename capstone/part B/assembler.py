import sys
import re

COMP_TABLE = {
    "0":   "0101010", "1":   "0111111", "-1":  "0111010",
    "D":   "0001100", "A":   "0110000", "M":   "1110000",
    "!D":  "0001101", "!A":  "0110001", "!M":  "1110001",
    "-D":  "0001111", "-A":  "0110011", "-M":  "1110011",
    "D+1": "0011111", "A+1": "0110111", "M+1": "1110111",
    "D-1": "0001110", "A-1": "0110010", "M-1": "1110010",
    "D+A": "0000010", "D+M": "1000010",
    "D-A": "0010011", "D-M": "1010011",
    "A-D": "0000111", "M-D": "1000111",
    "D&A": "0000000", "D&M": "1000000",
    "D|A": "0010101", "D|M": "1010101",
}

DEST_TABLE = {
    "":    "000", "M":   "001", "D":   "010", "MD":  "011",
    "A":   "100", "AM":  "101", "AD":  "110", "AMD": "111",
}

JUMP_TABLE = {
    "":    "000", "JGT": "001", "JEQ": "010", "JGE": "011",
    "JLT": "100", "JNE": "101", "JLE": "110", "JMP": "111",
}

SYMBOL_PATTERN = re.compile(r"^[A-Za-z_.$:][A-Za-z0-9_.$:]*$")


def assemble(asm_path):
    symbols = {f"R{i}": i for i in range(16)}
    symbols.update({
        "SP": 0, "LCL": 1, "ARG": 2, "THIS": 3, "THAT": 4,
        "SCREEN": 16384, "KBD": 24576
    })

    with open(asm_path, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    instructions, errors, rom_addr = [], [], 0

    # Pass 1: Collect labels and check label syntax
    for line_num, raw in enumerate(raw_lines, start=1):
        code = "".join(raw.split("//", 1)[0].split())
        if not code:
            continue
        if code.startswith("(") or code.endswith(")"):
            if not (code.startswith("(") and code.endswith(")")) or len(code) < 3:
                errors.append(f"Line {line_num}: invalid label syntax '{code}'")
                continue
            label = code[1:-1]
            if not SYMBOL_PATTERN.match(label):
                errors.append(f"Line {line_num}: invalid label name '{label}'")
                continue
            if label in symbols:
                errors.append(f"Line {line_num}: duplicate label '{label}'")
                continue
            symbols[label] = rom_addr
        else:
            instructions.append((line_num, code))
            rom_addr += 1

    # Pass 2: Convert instructions to 16-bit binary (K mod 3 = 1 error reporting)
    next_var, machine_code = 16, []
    for line_num, code in instructions:
        if code.startswith("@"):
            operand = code[1:]
            if not operand:
                errors.append(f"Line {line_num}: invalid instruction '{code}'")
                continue
            if operand.isdigit():
                val = int(operand)
                if val < 0 or val > 32767:
                    errors.append(f"Line {line_num}: address out of range '{code}'")
                    continue
            else:
                if not SYMBOL_PATTERN.match(operand):
                    errors.append(f"Line {line_num}: invalid symbol '{operand}'")
                    continue
                if operand not in symbols:
                    symbols[operand] = next_var
                    next_var += 1
                val = symbols[operand]
            machine_code.append(f"0{val:015b}")
        else:
            dest_part, jump_part = "", ""
            expr = code
            if "=" in expr:
                dest_part, expr = expr.split("=", 1)
                if not dest_part or dest_part not in DEST_TABLE:
                    errors.append(f"Line {line_num}: invalid instruction '{code}'")
                    continue
            if ";" in expr:
                expr, jump_part = expr.split(";", 1)
                if not jump_part or jump_part not in JUMP_TABLE:
                    errors.append(f"Line {line_num}: invalid instruction '{code}'")
                    continue
            if expr not in COMP_TABLE:
                errors.append(f"Line {line_num}: invalid instruction '{code}'")
                continue
            machine_code.append(f"111{COMP_TABLE[expr]}{DEST_TABLE[dest_part]}{JUMP_TABLE[jump_part]}")

    if errors:
        for err in errors:
            print(err)
        print("Assembly failed. No hack file generated.")
        return False

    out_path = asm_path.rsplit(".", 1)[0] + ".hack"
    with open(out_path, "w", encoding="utf-8") as out_f:
        out_f.write("\n".join(machine_code) + "\n")

    with open("symbol.txt", "w", encoding="utf-8") as sym_f:
        for sym, addr in symbols.items():
            sym_f.write(f"{sym} = {addr}\n")

    print(f"Assembly successful! Output: {out_path}")
    return True


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python assembler.py <file.asm>")
        sys.exit(1)
    if not assemble(sys.argv[1]):
        sys.exit(1)
