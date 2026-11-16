#!/usr/bin/env python3
"""Fuente unica del proyecto: genera el Ladder (lista de instrucciones),
la tabla de variables, los comentarios de dispositivos y la tabla HMI.

Uso:  python tools/generate.py      (desde la raiz del repo)
"""
import csv
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ZONES = (1, 2, 3, 4)


# --------------------------------------------------------------------------
# Mapa de direcciones por zona
# --------------------------------------------------------------------------
def zm(n):
    """Direcciones de la zona n."""
    b = 30 + 10 * (n - 1)
    return dict(
        x=2 + n - 1, sol=500 + n - 1, b=b,
        sp=210 + n - 1, pv=0 + n - 1, pvv=4 + n - 1,
        des=8 + n - 1, dab=12 + n - 1, tw=10 + n - 1,
        ot=70 + n - 1, esp=74 + n - 1,
    )


# --------------------------------------------------------------------------
# Tabla de variables: (nombre, direccion, tipo, grupo, descripcion, HMI)
# HMI: R = solo lectura, W = escribe la HMI, RW = ambas, - = interna
# --------------------------------------------------------------------------
V = []


def var(name, addr, typ, group, desc, hmi="-"):
    V.append((name, addr, typ, group, desc, hmi))


var("ORDEN_MARCHA_FISICA", "X0", "BOOL", "Entrada", "Selector de marcha mantenido. 1 = operador pide marcha", "R")
var("CADENA_SEGURIDAD", "X1", "BOOL", "Entrada", "Cadena de emergencia. Contacto NC: 1 = OK, 0 = emergencia o cable cortado", "R")
for n in ZONES:
    var(f"HAB_FISICA_Z{n}", f"X{1 + n}", "BOOL", "Entrada", f"Habilitacion fisica zona {n} (1 = habilitada)", "R")
var("RESET_FISICO", "X6", "BOOL", "Entrada", "Pulsador de reset NO (rearme / reset de fallas)", "R")
var("FALLA_VFD", "X7", "BOOL", "Entrada", "Rele de falla del variador. 1 = falla (ver nota de polaridad en README)", "R")
var("ORDEN_MARCHA_VFD", "Y0", "BOOL", "Salida", "Orden de marcha al variador. Solo con AUTORIZACION_VARIADOR y MARCHA_SOSTENIDA", "R")
var("HAB_CALENTADORES", "Y1", "BOOL", "Salida", "Habilita la potencia de calentamiento (sin emergencia, sin sobretemperatura, >=1 zona habilitada)", "R")
var("RESET_FALLA_VFD", "Y2", "BOOL", "Salida", "Pulso de reset hacia el variador (duracion TIEMPO_RESET_VFD)", "R")
var("ALARMA_GENERAL_OUT", "Y3", "BOOL", "Salida", "Baliza/bocina: refleja ALARMA_GENERAL", "R")

# ---- Marcas generales (no retentivas)
var("SEGURIDAD_OK", "M0", "BOOL", "Seguridad", "Copia de X1: cadena de seguridad cerrada", "R")
var("EMERGENCIA_ACTIVA", "M1", "BOOL", "Seguridad", "Emergencia activa (X1 = 0)", "R")
var("REARME_REQUERIDO", "M2", "BOOL", "Seguridad", "Se pone al energizar y ante emergencia. Se borra con reset si X1=1 y X0=0", "R")
var("PULSO_RESET", "M3", "BOOL", "Seguridad", "Pulso de 1 scan por X6 o M90", "-")
var("FLANCO_X0", "M21", "BOOL", "Control", "Pulso de 1 scan al subir X0", "-")
var("FALLA_LATCH", "M6", "BOOL", "Seguridad", "Falla del variador enclavada hasta reset", "R")
var("SOBRETEMP_LATCH", "M87", "BOOL", "Seguridad", "Sobretemperatura enclavada hasta reset", "R")
var("COMM_PV_OK", "M7", "BOOL", "Comunicacion", "Datos de temperatura frescos (latido PV vigente) o supervision desactivada", "R")
var("COMM_HMI_OK", "M8", "BOOL", "Comunicacion", "Latido de HMI vigente o supervision desactivada", "R")
var("FALLA_VFD_ESPEJO", "M9", "BOOL", "Diagnostico", "Copia de X7 para la HMI", "R")
var("PULSO_DATO_PV", "M10", "BOOL", "Comunicacion", "Cambio detectado en PV_HEARTBEAT (1 scan)", "-")
var("PULSO_DATO_HMI", "M11", "BOOL", "Comunicacion", "Cambio detectado en HMI_HEARTBEAT (1 scan)", "-")
var("ANY_ZONA_HAB", "M12", "BOOL", "Control", "Al menos una zona habilitada", "R")
var("ALGUNA_ZONA_BLOQUEA", "M13", "BOOL", "Control", "Alguna zona habilitada impide la marcha", "R")
var("ALGUNA_SOBRETEMP", "M14", "BOOL", "Control", "Alguna PV valida supera LIMITE_SOBRETEMP", "R")
var("AUTORIZACION_VARIADOR", "M16", "BOOL", "Control", "Permiso general de marcha (todas las condiciones)", "R")
var("MARCHA_SOSTENIDA", "M17", "BOOL", "Control", "Marcha en curso. Arranca con FLANCO_X0 + autorizacion; cae si cae la autorizacion", "R")
var("MARCHA_BLOQUEADA", "M18", "BOOL", "Control", "Operador pide marcha (X0) pero no hay autorizacion", "R")
var("ALARMA_GENERAL", "M19", "BOOL", "Alarmas", "Cualquier alarma activa", "R")
var("RESET_VFD_EN_CURSO", "M20", "BOOL", "Control", "Pulso de reset al variador en curso", "R")
var("ALM_COMM_PV", "M81", "BOOL", "Alarmas", "Sin datos de temperatura (timeout)", "R")
var("ALM_COMM_HMI", "M82", "BOOL", "Alarmas", "Sin latido de HMI (timeout)", "R")
var("ALM_NINGUNA_ZONA", "M84", "BOOL", "Alarmas", "Ninguna zona habilitada", "R")
var("PV_HB_VISTO", "M85", "BOOL", "Comunicacion", "Se recibio al menos un latido PV desde el ultimo timeout", "-")
var("HMI_HB_VISTO", "M86", "BOOL", "Comunicacion", "Se recibio al menos un latido HMI desde el ultimo timeout", "-")
var("INIT_PULSO", "M89", "BOOL", "Sistema", "Scan de inicializacion de parametros", "-")
var("RESET_HMI", "M90", "BOOL", "HMI", "Boton de reset en pantalla (accion SET; el PLC lo borra)", "W")

# ---- Marcas por zona
ZN = [("ZONA_HABILITADA", "Zona habilitada = X fisica AND solicitud HMI"),
      ("ZONA_SIN_HAB_FISICA", "HMI pide la zona pero falta la habilitacion fisica"),
      ("SP_VALIDO", "SP_MINIMO <= SP <= SP_MAXIMO"),
      ("PV_VALIDA", "PV fresca (COMM_PV_OK) y dentro de rango plausible"),
      ("ZONA_EN_VENTANA", "|PV-SP| <= BANDA_TOLERANCIA"),
      ("ZONA_LISTA", "En ventana durante TIEMPO_ESTABILIDAD"),
      ("VENTANA_ADMITIDA", "ZONA_LISTA, o marcha en curso, o EXIGIR_VENTANA=0"),
      ("ZONA_BLOQUEA", "Zona habilitada con SP invalido, PV invalida o fuera de ventana"),
      ("ALM_SP_INVALIDO", "Zona habilitada con SP fuera de limites"),
      ("ALM_PV_INVALIDA", "Zona habilitada sin PV valida")]
for n in ZONES:
    z = zm(n)
    for i, (nm, ds) in enumerate(ZN):
        var(f"{nm}_Z{n}", f"M{z['b'] + i}", "BOOL", f"Zona {n}", ds, "R")
for n in ZONES:
    var(f"ALM_SOBRETEMP_Z{n}", f"M{zm(n)['ot']}", "BOOL", f"Zona {n}", "PV valida > LIMITE_SOBRETEMP", "R")
for n in ZONES:
    var(f"HAB_FISICA_ESPEJO_Z{n}", f"M{zm(n)['esp']}", "BOOL", f"Zona {n}", "Copia de la entrada de habilitacion para la HMI", "R")

# ---- Marcas retentivas (M500+, retentivas por defecto en FX3U: verificar en el L02)
for n in ZONES:
    var(f"SOLICITUD_HMI_Z{n}", f"M{500 + n - 1}", "BOOL", "HMI (retentiva)", f"Solicitud de habilitacion zona {n} desde la HMI (boton alternado)", "RW")
var("EXIGIR_VENTANA", "M504", "BOOL", "Config (retentiva)", "1 = para arrancar cada zona habilitada debe estar estable dentro de la banda", "RW")
var("CONFIG_INICIALIZADA", "M505", "BOOL", "Config (retentiva)", "1 = parametros ya cargados. Poner a 0 restaura valores por defecto", "-")
var("PV_HB_EN", "M506", "BOOL", "Config (retentiva)", "1 = supervisar latido PV (recomendado). 0 = solo rango plausible (RIESGO)", "-")
var("HMI_HB_EN", "M507", "BOOL", "Config (retentiva)", "1 = supervisar latido de HMI", "-")

# ---- Registros
D_CFG = [("SP_MINIMO", 200, 50, "Minimo SP permitido (0,1 C). Inicial 5,0 C"),
         ("SP_MAXIMO", 201, 3500, "Maximo SP permitido (0,1 C)"),
         ("BANDA_TOLERANCIA", 202, 50, "Banda |PV-SP| para ventana de arranque (0,1 C)"),
         ("TIEMPO_ESTABILIDAD", 203, 300, "Permanencia en banda (0,1 s). 300 = 30 s"),
         ("TIMEOUT_COMM_PV", 204, 50, "Sin latido PV (0,1 s). 50 = 5 s"),
         ("PV_MIN_PLAUSIBLE", 205, -200, "PV minima valida (0,1 C)"),
         ("PV_MAX_PLAUSIBLE", 206, 5000, "PV maxima valida (0,1 C). Debe ser >= LIMITE_SOBRETEMP"),
         ("TIMEOUT_HMI", 207, 100, "Sin latido HMI (0,1 s). 100 = 10 s"),
         ("LIMITE_SOBRETEMP", 208, 4000, "Sobretemperatura absoluta (0,1 C)"),
         ("TIEMPO_RESET_VFD", 209, 10, "Duracion del pulso de reset al variador (0,1 s)")]
for nm, a, dv, ds in D_CFG:
    var(nm, f"D{a}", "INT16", "Config (retentivo)", f"{ds}. Defecto {dv}", "RW")
for n in ZONES:
    var(f"SP_ZONA_{n}", f"D{209 + n}", "INT16", "Proceso (retentivo)", f"Setpoint zona {n} (0,1 C). Escribe la HMI. Inicial 0 = invalido hasta que se cargue", "RW")
for n in ZONES:
    var(f"PV_CRUDA_Z{n}", f"D{n - 1}", "INT16", "Proceso", f"Temperatura zona {n} recibida (0,1 C). La escribe el gateway/HMI", "W")
for n in ZONES:
    var(f"PV_ZONA_{n}", f"D{3 + n}", "INT16", "Proceso", f"PV para mostrar: PV_CRUDA si es valida, -9999 si no (nunca un dato viejo)", "R")
for n in ZONES:
    var(f"DESVIO_Z{n}", f"D{7 + n}", "INT16", "Proceso", f"PV - SP zona {n} (0,1 C)", "R")
for n in ZONES:
    var(f"DESVIO_ABS_Z{n}", f"D{11 + n}", "INT16", "Proceso", f"|PV - SP| zona {n} (0,1 C)", "-")
var("HMI_HEARTBEAT", "D20", "INT16", "Comunicacion", "Contador que la HMI cambia periodicamente", "W")
var("HMI_HEARTBEAT_COPIA", "D21", "INT16", "Comunicacion", "Ultima copia vista por el PLC", "-")
var("PV_HEARTBEAT", "D22", "INT16", "Comunicacion", "Contador que el gateway/HMI cambia con cada actualizacion de PV", "W")
var("PV_HEARTBEAT_COPIA", "D23", "INT16", "Comunicacion", "Ultima copia vista por el PLC", "-")
var("MINUTOS_MARCHA", "D24", "INT16", "Diagnostico", "Minutos con Y0 activa desde el arranque del PLC", "R")
var("SEGUNDOS_AUX", "D25", "INT16", "Diagnostico", "Auxiliar del contador de minutos", "-")
var("MOTIVO_BLOQUEO", "D30", "INT16", "Diagnostico", "Codigo del motivo por el que no se permite la marcha (ver tabla)", "R")
var("ESTADO_VARIADOR", "D31", "INT16", "Diagnostico", "0=parado 1=marcha 2=falla 3=bloqueado", "R")

# ---- Timers
var("T_COMM_PV", "T0", "TIMER 100ms", "Temporizador", "Timeout de latido PV (valor en D204)", "-")
var("T_COMM_HMI", "T1", "TIMER 100ms", "Temporizador", "Timeout de latido HMI (valor en D207)", "-")
var("T_RESET_VFD", "T2", "TIMER 100ms", "Temporizador", "Duracion del pulso de reset (valor en D209)", "-")
for n in ZONES:
    var(f"T_ESTAB_Z{n}", f"T{9 + n}", "TIMER 100ms", "Temporizador", f"Estabilidad zona {n} (valor en D203)", "-")

# ---- Marcas especiales usadas
var("M8000", "M8000", "BOOL", "Sistema", "ON durante RUN", "-")
var("M8002", "M8002", "BOOL", "Sistema", "Pulso del primer scan en RUN", "-")
var("M8013", "M8013", "BOOL", "Sistema", "Reloj de 1 s", "-")

MOTIVOS = {
    0: "Sin bloqueo (marcha permitida o en marcha)",
    1: "Parada de emergencia",
    2: "Rearme requerido (X0 a OFF y pulsar reset)",
    3: "Falla del variador (resetear)",
    4: "Sobretemperatura (resetear)",
    5: "Ninguna zona habilitada",
    6: "Sin datos de temperatura (comunicacion)",
    7: "Zona 1 impide la marcha (SP, PV o calentando)",
    8: "Zona 2 impide la marcha",
    9: "Zona 3 impide la marcha",
    10: "Zona 4 impide la marcha",
    11: "Esperando orden de marcha (X0 en OFF)",
    12: "Condiciones OK: llevar X0 a OFF y de nuevo a ON para arrancar",
}


# --------------------------------------------------------------------------
# Programa Ladder en lista de instrucciones
# --------------------------------------------------------------------------
L = []


def seg(title):
    L.append("")
    L.append(f"## {title}")


def c(txt):
    L.append(f"; {txt}")


def i(txt):
    L.append(txt)


# ---- Segmento 1
seg("SEGMENTO 1 - INICIALIZACION (solo la primera vez o al poner M505 a 0)")
c("M89 vale 1 durante un unico scan; cada carga es una rama independiente")
i("LDI M505"); i("OUT M89")
for nm, a, dv, _ in D_CFG:
    c(nm)
    i("LD M89"); i(f"MOV K{dv} D{a}")
c("Banderas de configuracion por defecto")
for m in (504, 506, 507):
    i("LD M89"); i(f"SET M{m}")
i("LD M89"); i("SET M505")

# ---- Segmento 2
seg("SEGMENTO 2 - LECTURA DE ENTRADAS Y SEGURIDAD")
c("Cadena de seguridad: X1 es NC, 1 = OK")
i("LD X1"); i("OUT M0")
i("LDI X1"); i("OUT M1")
i("LD X7"); i("OUT M9")
c("Pulso de reset (fisico o HMI) y flanco de marcha")
i("LD X6"); i("OR M90"); i("PLS M3")
i("LD M3"); i("RST M90")
i("LD X0"); i("PLS M21")
c("Rearme obligatorio al energizar y ante emergencia. Se libera con reset, cadena OK y X0 = OFF")
i("LD M8002"); i("OR M1"); i("SET M2")
i("LD M3"); i("AND M0"); i("ANI X0"); i("RST M2")

# ---- Segmento 3
seg("SEGMENTO 3 - SUPERVISION DE COMUNICACION")
c("Latido PV: cualquier cambio de D22 reinicia el timeout T0")
i("LD<> D22 D23"); i("OUT M10")
i("LD M10"); i("MOV D22 D23")
i("LDI M10"); i("OUT T0 D204")
i("LD T0"); i("RST M85")
i("LD M10"); i("SET M85")
c("COMM_PV_OK = (latido visto Y sin timeout) O supervision desactivada")
i("LD M85"); i("ANI T0"); i("ORI M506"); i("OUT M7")
c("Latido HMI: igual, con D20/D21 y T1")
i("LD<> D20 D21"); i("OUT M11")
i("LD M11"); i("MOV D20 D21")
i("LDI M11"); i("OUT T1 D207")
i("LD T1"); i("RST M86")
i("LD M11"); i("SET M86")
i("LD M86"); i("ANI T1"); i("ORI M507"); i("OUT M8")

# ---- Segmentos 4 a 7
for n in ZONES:
    z = zm(n)
    b = z["b"]
    seg(f"SEGMENTO {3 + n} - ZONA {n}")
    c("Habilitacion: fisica Y solicitud HMI")
    i(f"LD X{z['x']}"); i(f"AND M{z['sol']}"); i(f"OUT M{b}")
    i(f"LD M{z['sol']}"); i(f"ANI X{z['x']}"); i(f"OUT M{b + 1}")
    i(f"LD X{z['x']}"); i(f"OUT M{z['esp']}")
    c("Validacion de SP y de PV (PV solo valida con comunicacion fresca)")
    i(f"LD>= D{z['sp']} D200"); i(f"AND<= D{z['sp']} D201"); i(f"OUT M{b + 2}")
    i("LD M7"); i(f"AND>= D{z['pv']} D205"); i(f"AND<= D{z['pv']} D206"); i(f"OUT M{b + 3}")
    c("PV para mostrar: dato valido o centinela -9999. Nunca se muestra un dato viejo como actual")
    i(f"LD M{b + 3}"); i(f"MOV D{z['pv']} D{z['pvv']}")
    i(f"LDI M{b + 3}"); i(f"MOV K-9999 D{z['pvv']}")
    c("Desvio y valor absoluto")
    i("LD M8000"); i(f"SUB D{z['pv']} D{z['sp']} D{z['des']}")
    i("LD M8000"); i(f"MOV D{z['des']} D{z['dab']}")
    i(f"LD< D{z['dab']} K0"); i(f"NEG D{z['dab']}")
    c("Ventana de estabilidad")
    i(f"LD M{b + 3}"); i(f"AND<= D{z['dab']} D202"); i(f"OUT M{b + 4}")
    i(f"LD M{b + 4}"); i(f"OUT T{z['tw']} D203")
    i(f"LD T{z['tw']}"); i(f"OUT M{b + 5}")
    i(f"LD M{b + 5}"); i("OR M17"); i("ORI M504"); i(f"OUT M{b + 6}")
    c("La zona bloquea solo si esta habilitada. Una zona deshabilitada no bloquea")
    i(f"LDI M{b + 2}"); i(f"ORI M{b + 3}"); i(f"ORI M{b + 6}"); i(f"AND M{b}"); i(f"OUT M{b + 7}")
    c("Alarmas de la zona")
    i(f"LD M{b}"); i(f"ANI M{b + 2}"); i(f"OUT M{b + 8}")
    i(f"LD M{b}"); i(f"ANI M{b + 3}"); i(f"OUT M{b + 9}")
    i(f"LD M{b + 3}"); i(f"AND> D{z['pv']} D208"); i(f"OUT M{z['ot']}")

# ---- Segmento 8
seg("SEGMENTO 8 - RESUMEN DE ZONAS Y LATCHES DE FALLA")
i("LD M30"); i("OR M40"); i("OR M50"); i("OR M60"); i("OUT M12")
i("LD M37"); i("OR M47"); i("OR M57"); i("OR M67"); i("OUT M13")
i("LD M70"); i("OR M71"); i("OR M72"); i("OR M73"); i("OUT M14")
c("Falla del variador y sobretemperatura: se enclavan y solo se liberan con reset manual")
i("LD X7"); i("SET M6")
i("LD M3"); i("ANI X7"); i("RST M6")
i("LDF M20"); i("ANI X7"); i("RST M6")
i("LD M14"); i("SET M87")
i("LD M3"); i("ANI M14"); i("RST M87")
c("Reset al variador: pulso de TIEMPO_RESET_VFD si X7 = 1 al pulsar reset")
i("LD M3"); i("AND X7"); i("SET M20")
i("LD T2"); i("RST M20")
i("LD M20"); i("OUT T2 D209")
i("LD M20"); i("OUT Y2")

# ---- Segmento 9 / 10
seg("SEGMENTO 9 - AUTORIZACION GENERAL")
c("AUTORIZACION = X0 AND seguridad AND sin rearme AND sin fallas AND >=1 zona AND ninguna zona bloquea AND datos PV frescos")
i("LD X0"); i("AND M0"); i("ANI M2"); i("ANI M6"); i("ANI M87"); i("ANI M14")
i("AND M12"); i("ANI M13"); i("AND M7"); i("OUT M16")
i("LD X0"); i("ANI M16"); i("OUT M18")

seg("SEGMENTO 10 - CONTROL DEL VARIADOR")
c("Arranque solo con flanco de X0 y autorizacion. Cualquier perdida de autorizacion corta y exige nuevo flanco")
i("LD M21"); i("AND M16"); i("SET M17")
i("LDI M16"); i("RST M17")
i("LD M16"); i("AND M17"); i("OUT Y0")
c("Calentadores: sin emergencia, sin sobretemperatura, con al menos una zona habilitada")
i("LD M0"); i("ANI M87"); i("ANI M14"); i("AND M12"); i("OUT Y1")
c("Contador de minutos de marcha")
i("LD M8013"); i("AND Y0"); i("INCP D25")
i("LD>= D25 K60"); i("INCP D24")
i("LD>= D25 K60"); i("MOVP K0 D25")

# ---- Segmento 11
seg("SEGMENTO 11 - ALARMAS Y DIAGNOSTICO")
i("LDI M7"); i("OUT M81")
i("LDI M8"); i("OUT M82")
i("LDI M12"); i("OUT M84")
c("ALARMA_GENERAL")
i("LD M1"); i("OR M6"); i("OR M87"); i("OR M81"); i("OR M82")
for n in ZONES:
    b = zm(n)["b"]
    i(f"OR M{b + 8}"); i(f"OR M{b + 9}")
i("OUT M19")
i("LD M19"); i("OUT Y3")
c("MOTIVO_BLOQUEO (D30): se escribe de menor a mayor prioridad; la ultima condicion cierta gana")
i("LD M8000"); i("MOV K0 D30")
i("LDI X0"); i("MOV K11 D30")
i("LD M16"); i("ANI M17"); i("MOV K12 D30")
for n in (4, 3, 2, 1):
    i(f"LD M{zm(n)['b'] + 7}"); i(f"MOV K{6 + n} D30")
i("LDI M12"); i("MOV K5 D30")
i("LDI M7"); i("MOV K6 D30")
i("LD M14"); i("OR M87"); i("MOV K4 D30")
i("LD M6"); i("MOV K3 D30")
i("LD M2"); i("MOV K2 D30")
i("LD M1"); i("MOV K1 D30")
c("ESTADO_VARIADOR (D31)")
i("LD M8000"); i("MOV K0 D31")
i("LD M18"); i("MOV K3 D31")
i("LD Y0"); i("MOV K1 D31")
i("LD M6"); i("OR X7"); i("MOV K2 D31")

seg("SEGMENTO 12 - ENLACE CON HMI")
c("No requiere codigo: la HMI lee/escribe directamente M, D, X, Y listados en docs/variables.csv.")
c("Escrituras de la HMI: M500-M504, M90, D200-D213, D0-D3, D20, D22.")
i("END")


# --------------------------------------------------------------------------
# Salidas
# --------------------------------------------------------------------------
def write(path, text):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


write("ladder/MAIN_comentado.il.txt",
      "; Programa MAIN - FX3U / Coolmay L02-24MT - lista de instrucciones\n"
      "; Las lineas que empiezan con ; o ## son comentarios para el lector.\n" + "\n".join(L) + "\n")
clean = [x for x in L if x and not x.startswith(";") and not x.startswith("##")]
write("ladder/MAIN_para_pegar.il.txt", "\n".join(clean) + "\n")

with open(os.path.join(ROOT, "docs", "variables.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Nombre", "Direccion", "Tipo", "Grupo", "Descripcion", "HMI"])
    w.writerows(V)

with open(os.path.join(ROOT, "gxworks2", "comentarios_dispositivos.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Dispositivo", "Comentario"])
    for name, addr, *_rest in V:
        if addr.startswith("M80"):
            continue
        w.writerow([addr, name])
