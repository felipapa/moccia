# Control de extrusora: 4 zonas + variador (PLC FX3U / Coolmay L02-24MT + HMI Coolmay)

Programa Ladder para GX Works2 (FX3U/FX3UC) que autoriza la marcha del variador solo cuando se cumplen todas las condiciones, supervisa cuatro zonas de temperatura y se integra con una HMI Coolmay.

> **Estado:** programa escrito y verificado de forma estática (dispositivos declarados, sin bobinas OUT duplicadas). **No fue probado en hardware.** Probalo primero con el variador desconectado de la potencia, siguiendo la lista de puesta en marcha de más abajo.

## Contenido

| Ruta | Qué es |
|---|---|
| `ladder/MAIN_para_pegar.il.txt` | Programa completo en lista de instrucciones, sin comentarios |
| `ladder/MAIN_comentado.il.txt` | El mismo programa con segmentos y comentarios |
| `docs/variables.csv` | Todas las variables: nombre, dirección, tipo, función, uso de HMI |
| `docs/hmi.md` | Qué objeto de la HMI apunta a qué registro |
| `docs/comunicacion.md` | Arquitectura de comunicación y mapa de registros |
| `gxworks2/comentarios_dispositivos.csv` | Comentarios de dispositivos (dirección, nombre) |
| `tools/generate.py` | Genera el programa y las tablas (fuente única) |
| `tools/check_program.py` | Verificación estática |

`generate.py` es la fuente de verdad: si cambiás una dirección, editala ahí y volvé a correr `python tools/generate.py && python tools/check_program.py`.

## Cómo cargarlo en GX Works2

1. Proyecto nuevo, **Simple Project**, serie **FXCPU**, tipo **FX3U/FX3UC**, lenguaje **Ladder**.
2. Abrí `MAIN`. Cambiá a vista de **lista de instrucciones** (menú *Ver*, opción de lista) y pegá `MAIN_para_pegar.il.txt`. Al volver a Ladder el programa se dibuja y se convierte (F4).
3. Importá los comentarios con *Proyecto → Importar archivo → Comentarios comunes de dispositivo*, o cargalos a mano desde `variables.csv`. Si el formato de importación no coincide, exportá uno vacío desde GX Works2 y copiá las columnas.
4. **Parámetro de PLC → Configuración de dispositivos:** verificá que `M500` en adelante y `D200` en adelante sean **retentivos** en tu L02-24MT. Si no, ajustalo o cambiá las direcciones en `generate.py`.
5. Compilá (*Convertir → Reconstruir todo*). No debe haber errores. Transferí al PLC.

> Los archivos `.gxw` no se generan por código: es un formato propietario. Este repo contiene el contenido necesario para recrearlo.

## Mapa de E/S

| Dirección | Nombre | Notas |
|---|---|---|
| X0 | ORDEN_MARCHA_FISICA | Selector **mantenido** |
| X1 | CADENA_SEGURIDAD | Contacto **NC**: 1 = OK |
| X2 a X5 | HAB_FISICA_Z1 a Z4 | 1 = zona habilitada |
| X6 | RESET_FISICO | Pulsador NO |
| X7 | FALLA_VFD | 1 = falla |
| Y0 | ORDEN_MARCHA_VFD | Orden de marcha |
| Y1 | HAB_CALENTADORES | Habilitación de potencia de calor |
| Y2 | RESET_FALLA_VFD | Pulso de reset al variador |
| Y3 | ALARMA_GENERAL_OUT | Baliza/bocina |

## Lógica

**Autorización** (`M16`):

```
X0 AND SEGURIDAD_OK AND NOT REARME_REQUERIDO AND NOT FALLA_LATCH
   AND NOT SOBRETEMP_LATCH AND NOT SOBRETEMP_ACTUAL
   AND ALGUNA_ZONA_HABILITADA AND NOT ALGUNA_ZONA_BLOQUEA AND COMM_PV_OK
```

**Marcha** (`Y0`) = `AUTORIZACION AND MARCHA_SOSTENIDA`. `MARCHA_SOSTENIDA` se activa solo con un **flanco ascendente de X0** mientras hay autorización, y se borra apenas la autorización cae. Por eso:

- Al energizar con X0 ya en ON **no** arranca.
- Tras cualquier falla hay que llevar X0 a OFF y de nuevo a ON.
- No hay enclavamiento que sostenga la marcha si una condición obligatoria desaparece.

**Zonas** (cada una igual):

- `ZONA_HABILITADA = X fisica AND solicitud HMI`. La HMI solo *pide*; el PLC exige la señal física.
- Una zona **deshabilitada no bloquea** la marcha.
- Una zona **habilitada** bloquea si: SP fuera de `[SP_MINIMO, SP_MAXIMO]`, PV inválida o sin comunicación, o (con `EXIGIR_VENTANA` = 1) todavía no estuvo `TIEMPO_ESTABILIDAD` dentro de `BANDA_TOLERANCIA`.
- Se exige **al menos una zona habilitada**.
- La ventana de estabilidad solo se exige para **arrancar**; ya en marcha no detiene por desvío. La sobretemperatura sí detiene.

**Emergencia:** `X1 = 0` corta la autorización y los calentadores. Al energizar y tras una emergencia queda `REARME_REQUERIDO` hasta que X1 = 1, X0 = OFF y se pulsa reset. No hay rearranque automático.

### Comportamiento ante fallas

| Situación | Detección | Acción del PLC | Se libera con |
|---|---|---|---|
| Emergencia | X1 = 0 | Corta marcha y calentadores, rearme requerido | X1 = 1, X0 OFF, reset |
| Falla del variador | X7 = 1 | Corta marcha, `FALLA_LATCH`, pulso de reset al variador al pulsar reset | Reset con falla ya limpia, o fin del pulso de reset con X7 = 0 |
| Sobretemperatura | PV válida > `LIMITE_SOBRETEMP` | Corta marcha y calentadores, `SOBRETEMP_LATCH` | Reset con temperatura bajo el límite |
| Sin datos de temperatura | Sin cambio de `PV_HEARTBEAT` durante `TIMEOUT_COMM_PV` | `COMM_PV_OK` = 0: corta la marcha; las PV pasan a -9999 | Vuelve el latido y se re-arranca con X0 |
| PV fuera de rango (sensor abierto) | Fuera de `[PV_MIN, PV_MAX]` | PV inválida: bloquea si la zona está habilitada | Dato válido |
| SP inválido | Fuera de límites | Bloquea si la zona está habilitada | SP válido |
| Pérdida de HMI | Sin cambio de `HMI_HEARTBEAT` | Solo alarma. La máquina sigue, no depende de la HMI | Vuelve el latido |
| Reinicio del PLC | `M8002` | Rearme requerido, sin autoarranque | Reset |
| Zona pedida sin habilitación física | HMI ON y X = 0 | Zona no habilitada, indicador en HMI | Habilitación física |

`MOTIVO_BLOQUEO` (D30) resume la causa de mayor prioridad:

| Código | Motivo |
|---|---|
| 0 | Sin bloqueo |
| 1 | Emergencia |
| 2 | Rearme requerido |
| 3 | Falla del variador |
| 4 | Sobretemperatura |
| 5 | Ninguna zona habilitada |
| 6 | Sin datos de temperatura |
| 7 a 10 | Zona 1 a 4 impide la marcha |
| 11 | Esperando orden de marcha (X0 en OFF) |
| 12 | Condiciones OK: llevar X0 a OFF y de nuevo a ON |

## Supuestos que tenés que confirmar

No pude leer el programa Ladder de tu `Extrusora_Completa.gxw` (formato propietario). Tomé los nombres de tus etiquetas y asumí lo siguiente. Si algo no coincide, cambialo en `tools/generate.py`.

1. **Unidades:** temperaturas enteras en **décimas de grado** (250 = 25,0 °C). `SP_MINIMO` inicial = 50 (5,0 °C). La HMI debe mostrarlas con un decimal.
2. **X1 es NC** y **X7 vale 1 en falla**. Para X7 es más seguro cablear un contacto NC del variador y negar la lógica, así un cable cortado también dispara. Si lo hacés, cambiá en el Ladder los usos de `X7`.
3. **Comunicación de temperaturas:** el PLC espera que las PV lleguen **escritas en D0 a D3** junto con un contador `PV_HEARTBEAT` (D22) que cambia en cada actualización. Quién lo escribe (HMI como pasarela o un maestro Modbus) depende de tu hardware: ver `docs/comunicacion.md`.
4. **Supervisión de latido:** viene activada por defecto (`PV_HB_EN` = 1). Si tu pasarela no puede generar el contador, el PLC bloquea la marcha por "sin datos". Podés poner `M506` en 0, pero entonces un dato congelado se vería como actual: solo se detecta por rango. Es un riesgo, decidilo con criterio.
5. **Ventana de estabilidad activa por defecto** (`EXIGIR_VENTANA` = 1), como indicaban tus etiquetas. Para probar sin calentar, ponela en 0 desde la HMI.
6. **Direcciones retentivas:** M500+ y D200+ se asumen retentivas (valor por defecto en FX3U). Verificalo en el L02.
7. **Setpoints iniciales en 0:** quedan inválidos hasta que el operador los cargue.

## Seguridad

La parada de emergencia **no puede depender solo del PLC**. Debe existir un circuito de seguridad independiente (relé de seguridad o contactor de corte de potencia con la categoría que exija el análisis de riesgos de la máquina) que corte la potencia del variador y de los calentadores. El PLC solo **supervisa** esa cadena a través de X1 y no sustituye al relé de seguridad. El análisis de riesgo y la validación final son responsabilidad del integrador.

## Puesta en marcha (sin potencia)

1. Con el variador sin potencia, forzá las entradas y verificá `D30` en cada caso.
2. X1 = 0: `M1` = 1, `Y0` = 0, `Y1` = 0. Al volver X1 = 1 sigue en rearme hasta X0 OFF + reset.
3. Zonas: habilitá Z1 por HMI **sin** X2: debe aparecer `ZONA_SIN_HAB_FISICA_Z1` y no habilitarse.
4. SP = 0 con la zona habilitada: `ALM_SP_INVALIDO` y `D30` = 7.
5. Detené el contador `D22`: a los `TIMEOUT_COMM_PV` debe caer `COMM_PV_OK` y las PV mostrar -9999.
6. Subí PV por encima de `LIMITE_SOBRETEMP`: corta y enclava.
7. Con todo OK: X0 OFF → ON arranca `Y0`. Quitá cualquier condición: `Y0` cae y para volver a arrancar hay que ciclar X0.
8. Recién entonces conectá potencia, con la emergencia cableada y probada.
