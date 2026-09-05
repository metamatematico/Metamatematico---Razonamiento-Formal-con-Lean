# -*- coding: utf-8 -*-
"""La capa de sintaxis: la notacion de la consulta como arbol.

    revisar(consulta) -> Revision    lo que pide el resto del sistema
    extraer(texto)    -> [Tramo]     donde esta la notacion
    bien_formada(q)   -> Diagnostico si esta bien escrita, y si no, por que
    rasgos_de_consulta(q) -> dict    los rasgos del arbol, para el emparejador

Las dos cifras que gobiernan esta capa, medidas sobre los 23 243 enunciados de
LeanWorkbook: rechaza el 3,6 % de lo que esta bien y caza el 60,8 % de lo que
se rompe a proposito (99 % si la rotura es un delimitador). Ver
`scripts/sintaxis_falsos_positivos.py`.
"""
from nucleo.sintaxis.arbol import Diagnostico, Nodo, bien_formada, parsear
from nucleo.sintaxis.lexico import Tramo, extraer, tokenizar
from nucleo.sintaxis.rasgos import rasgos_de_arbol, rasgos_de_consulta
from nucleo.sintaxis.revision import Revision, revisar

__all__ = ["Diagnostico", "Nodo", "Revision", "Tramo", "bien_formada",
           "extraer", "parsear", "rasgos_de_arbol", "rasgos_de_consulta",
           "revisar", "tokenizar"]
