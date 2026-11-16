# Configuración de la HMI Coolmay

Driver: PLC Mitsubishi serie FX, con los parámetros serie iguales a los del PLC. Los nombres exactos de los objetos cambian según la versión del software de la HMI: usá el equivalente. Temperaturas: **entero con signo de 16 bits, 1 decimal**.

## Pantalla principal

| Objeto | Tipo | Dirección | Notas |
|---|---|---|---|
| Emergencia | Lámpara | M1 | Roja |
| Rearme requerido | Lámpara | M2 | |
| Autorización de marcha | Lámpara | M16 | |
| Variador en marcha | Lámpara | Y0 | |
| Falla del variador | Lámpara | M6 | |
| Estado del variador | Lista de textos | D31 | 0 Parado, 1 Marcha, 2 Falla, 3 Bloqueado |
| Comunicación PV | Lámpara | M7 | Verde = OK |
| Comunicación HMI | Lámpara | M8 | |
| Motivo de bloqueo | Lista de textos | D30 | Textos 0 a 12 de `README.md` |
| Minutos de marcha | Numérico | D24 | |
| Botón reset | Botón, acción **SET** | M90 | El PLC lo borra solo |
| Exigir ventana | Interruptor | M504 | |

## Panel de zonas (repetir para Z1 a Z4)

| Objeto | Z1 | Z2 | Z3 | Z4 | Tipo |
|---|---|---|---|---|---|
| Botón de habilitación | M500 | M501 | M502 | M503 | Botón **alternado** |
| Habilitación física | M74 | M75 | M76 | M77 | Lámpara |
| Zona habilitada | M30 | M40 | M50 | M60 | Lámpara |
| Pedida sin hab. física | M31 | M41 | M51 | M61 | Lámpara |
| Setpoint | D210 | D211 | D212 | D213 | Entrada numérica |
| Temperatura real | D4 | D5 | D6 | D7 | Numérico (-9999 = sin dato) |
| Desvío | D8 | D9 | D10 | D11 | Numérico |
| En ventana | M34 | M44 | M54 | M64 | Lámpara |
| Lista | M35 | M45 | M55 | M65 | Lámpara |
| Sobretemperatura | M70 | M71 | M72 | M73 | Lámpara |

Límites de la entrada de SP: la HMI puede limitar visualmente a 5,0 a 350,0, pero **el PLC es quien valida** con `SP_MINIMO` y `SP_MAXIMO`.

## Panel de alarmas

| Alarma | Dirección |
|---|---|
| Emergencia | M1 |
| Sin datos de temperatura | M81 |
| Sin comunicación HMI | M82 |
| Falla del variador | M6 |
| Sobretemperatura | M87 |
| Ninguna zona habilitada | M84 |
| SP inválido Z1 a Z4 | M38, M48, M58, M68 |
| PV inválida Z1 a Z4 | M39, M49, M59, M69 |
| Marcha bloqueada | M18 |
| Alarma general | M19 |

## Pantalla de configuración (con contraseña)

| Parámetro | Dirección |
|---|---|
| SP mínimo, SP máximo | D200, D201 |
| Banda, tiempo de estabilidad | D202, D203 |
| Timeout PV, timeout HMI | D204, D207 |
| PV mín./máx. plausible | D205, D206 |
| Límite de sobretemperatura | D208 |
| Pulso de reset al variador | D209 |

## Funciones que la HMI debe ejecutar

- Copiar las 4 temperaturas del controlador a `D0 a D3` y cambiar `D22` en cada lectura (ver `comunicacion.md`).
- Cambiar `D20` periódicamente como latido.
