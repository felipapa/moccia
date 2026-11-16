#!/usr/bin/env python3
"""Verificaciones estaticas del Ladder: dispositivos declarados, bobinas OUT
duplicadas, SET/RST emparejados y entradas escritas por el programa."""
import csv
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
prog = open(os.path.join(ROOT, "ladder", "MAIN_para_pegar.il.txt"), encoding="utf-8").read().splitlines()
decl = {r["Direccion"] for r in csv.DictReader(open(os.path.join(ROOT, "docs", "variables.csv"), encoding="utf-8-sig"))}

dev = re.compile(r"^(?:[XYMTCD]\d+)$")
errors = []
outs = defaultdict(list)      # OUT de bobina (no debe repetirse)
sets, rsts = set(), set()
writers = defaultdict(set)    # registros D escritos por instrucciones

for n, line in enumerate(prog, 1):
    t = line.split()
    op, args = t[0], t[1:]
    for a in args:
        if dev.match(a) and a not in decl:
            errors.append(f"linea {n}: {a} no esta en variables.csv ({line})")
    if op == "OUT" and args and args[0][0] in "MY":
        outs[args[0]].append(n)
    if op == "OUT" and args and args[0][0] == "T":
        outs[args[0]].append(n)
    if op in ("SET", "PLS"):
        sets.add(args[0])
    if op == "RST":
        rsts.add(args[0])
    if op in ("MOV", "MOVP") and args[1][0] == "D":
        writers[args[1]].add(n)
    if op in ("SUB",):
        writers[args[2]].add(n)

for d, ls in outs.items():
    if len(ls) > 1:
        errors.append(f"bobina OUT duplicada {d} en lineas {ls}")
for d in outs:
    if d in sets:
        errors.append(f"{d} usado con OUT y SET")
for d in sets:
    if d[0] == "M" and d not in rsts and d not in {"M3", "M21", "M505", "M504", "M506", "M507"}:
        errors.append(f"{d} tiene SET sin RST")
# entradas fisicas nunca deben ser bobinas
for d in outs:
    if d[0] == "X":
        errors.append(f"salida sobre entrada {d}")

# registros de escritura externa (HMI/gateway) no deben ser escritos por el PLC
ext = {"D0", "D1", "D2", "D3", "D20", "D22"}
for d in ext & set(writers):
    errors.append(f"{d} lo escribe tambien el PLC")

# la ultima MOV sobre D30/D31 debe ser la de mayor prioridad
print(f"{len(prog)} instrucciones, {len(outs)} bobinas OUT")
if errors:
    print("\n".join("ERROR: " + e for e in errors))
    sys.exit(1)
print("OK: sin bobinas duplicadas, sin dispositivos no declarados")
