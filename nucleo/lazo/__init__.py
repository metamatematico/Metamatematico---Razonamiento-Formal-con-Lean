# -*- coding: utf-8 -*-
"""El lazo por pasos: el modelo propone una táctica, Lean la evalúa sobre un
estado de prueba, y lo que contesta condiciona la siguiente.

Paso 3 de la propuesta de arquitectura. Las piezas:

    filtros.py      lo que se rechaza ANTES de gastar Lean (invariantes I4, I6)
    retro.py        lo que el modelo ve de un estado, y cómo se lee lo que devuelve
    proponentes.py  quién propone tácticas, de más barato a más caro (D0, D3)
    mediador.py     la búsqueda: frontera, clasificación, memoria de fallos
    registro.py     cada intento, aceptado o no, a data/transiciones_vivas.jsonl

La regla que las gobierna es I1 + I2: sólo Lean crea flechas, y el veredicto
lo da el fichero, no la sesión.
"""
