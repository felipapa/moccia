# Comunicación

El programa Ladder **no contiene** instrucciones de comunicación. Trabaja sobre registros D y marcas M que otros equipos leen y escriben. Los parámetros serie (velocidad, paridad, dirección) **dependen de tus equipos y no los inventé**: tomalos de sus manuales.

## Arquitectura recomendada (A): la HMI como pasarela

```
 Controlador de temperatura  <--RS485 Modbus RTU-->  HMI Coolmay  <--puerto serie, protocolo Mitsubishi FX-->  PLC L02-24MT
   (maestro: la HMI)                                  COM2 / COM1                                              (esclavo)
```

- **HMI ↔ PLC:** en el software de la HMI elegí el driver de PLC Mitsubishi serie FX compatible con el puerto del L02. La HMI lee y escribe directamente M, D, X, Y. El PLC no necesita código.
- **HMI ↔ controlador de temperatura:** segundo puerto de la HMI como maestro Modbus RTU. El controlador es esclavo.
- La HMI debe **copiar** las 4 temperaturas a `D0 a D3` del PLC cada vez que las lea, y **cambiar** `D22` (por ejemplo, sumar 1) en cada actualización. Eso permite al PLC detectar un dato congelado.
- La HMI también debe cambiar `D20` periódicamente (latido HMI).

Esto requiere que tu modelo de HMI tenga dos puertos o un puerto con ambos protocolos y funciones de transferencia/incremento de datos. **Confirmalo en el manual de la HMI.**

## Alternativa (B): el PLC como maestro Modbus

Si el L02-24MT tiene un puerto RS485 con soporte maestro Modbus RTU (en FX3U se hace con `ADPRW` o `RS`, según la placa), el PLC lee el controlador y escribe él mismo `D0 a D3` y `D22`. **No está incluido en el programa** porque depende de la placa y del firmware: hay que confirmarlo en el manual del L02-24MT. Para integrarlo, agregá un segmento antes de la validación que lea los registros del controlador y haga `INC D22` por cada respuesta correcta. El resto del programa no cambia.

## Parámetros de comunicación a completar

| Enlace | Maestro | Esclavo | Interfaz | Protocolo | Velocidad | Datos/Paridad/Paro | Dirección |
|---|---|---|---|---|---|---|---|
| HMI ↔ PLC | HMI | PLC | (ver manual) | Mitsubishi FX serie | (igual en ambos) | (igual en ambos) | (según driver) |
| HMI ↔ temperaturas | HMI | Controlador | RS485 | Modbus RTU | (del controlador) | (del controlador) | (del controlador) |

## Mapa de registros del PLC

Todas las temperaturas son enteros de 16 bits con signo, en décimas de grado.

| Zona | SP (HMI escribe) | PV cruda (pasarela escribe) | PV mostrada (PLC) | Desvío |
|---|---|---|---|---|
| 1 | D210 | D0 | D4 | D8 |
| 2 | D211 | D1 | D5 | D9 |
| 3 | D212 | D2 | D6 | D10 |
| 4 | D213 | D3 | D7 | D11 |

| Función | Registro | Quién escribe |
|---|---|---|
| Latido PV | D22 | Pasarela (cambia en cada actualización) |
| Latido HMI | D20 | HMI (cambia periódicamente) |
| Parámetros | D200 a D209 | HMI (pantalla de configuración) |
| Motivo de bloqueo | D30 | PLC |
| Estado del variador | D31 | PLC |

**Mapeo del controlador de temperatura:** cargá aquí las direcciones Modbus del equipo cuando las tengas (`temperatura zona n` → `D(n-1)`). Si el controlador devuelve un valor especial ante sensor abierto (por ejemplo 32767), caerá fuera de `PV_MAX_PLAUSIBLE` y el PLC lo tomará como PV inválida.

## Tratamiento de errores

- Sin cambio de `D22` durante `TIMEOUT_COMM_PV` → `COMM_PV_OK` = 0, alarma `ALM_COMM_PV`, la marcha se corta y las PV pasan a -9999. El PLC nunca presenta un valor viejo como medición actual.
- Sin cambio de `D20` durante `TIMEOUT_HMI` → solo alarma `ALM_COMM_HMI`.
- Tras recuperar la comunicación, la marcha **no** vuelve sola: hay que ciclar X0.
