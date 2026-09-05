# -*- coding: utf-8 -*-
"""Lo que el resto del sistema pide a esta capa: una revisión de la consulta.

QUE DEVUELVE Y POR QUE ASI
--------------------------
Dos cosas distintas, que conviene no mezclar:

  · los RASGOS del árbol, que van al emparejador y no se le enseñan a nadie;
  · un AVISO para el alumno, que sólo se emite cuando merece la pena.

CUANDO SE AVISA, Y POR QUE SOLO ENTONCES
----------------------------------------
Medido sobre los 23 243 enunciados de LeanWorkbook —todos correctos— el
revisor rechaza el 3,6 %. Avisar en todos esos casos sería decirle a uno de
cada veintiocho alumnos que su enunciado está mal cuando no lo está, y eso
enseña a ignorar los avisos.

Pero el 3,6 % no se reparte igual entre los seis motivos:

    motivo                    falsos positivos    caza (rotura real)
    delimitador sin cerrar          0,6 %              99,1 %
    delimitador sin abrir           0,7 %              99,5 %
    ------------------------------------------------------------
    los otros cuatro juntos         2,3 %              ~50 %

Los delimitadores son otra cosa: casi nunca se equivocan y casi nunca fallan.
Y son justo el error que más caro sale, porque un paréntesis sin cerrar hace
que el modelo formalice una fórmula que no es la que el alumno escribió —y
Lean verifica esa otra tan contento, con lo que la respuesta sale con el sello
de «verificado» puesto sobre el enunciado equivocado—.

Así que se avisa SOLO de delimitadores. De lo demás se guarda el diagnóstico
en los metadatos, que es donde sirve para depurar sin gritarle a nadie.

NUNCA BLOQUEA. Ni siquiera con un delimitador descasado: el aviso acompaña a
la respuesta, no la sustituye. Con 6 de cada 1000 falsos positivos, bloquear
sería negarle el servicio a alguien que escribió bien.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from nucleo.sintaxis.arbol import bien_formada
from nucleo.sintaxis.lexico import extraer
from nucleo.sintaxis.rasgos import rasgos_de_arbol

#: Los dos motivos que se le enseñan al alumno. Ver la tabla de arriba.
MOTIVOS_QUE_SE_AVISAN = ("delimitador_sin_cerrar", "delimitador_sin_abrir")

_TEXTO_AVISO = (
    "⚠ Revisa los delimitadores del enunciado: %s. "
    "Sigo adelante con lo que he entendido, pero si no era eso, reescríbelo."
)


@dataclass
class Revision:
    """El resultado de mirar la consulta antes de gastar una llamada."""
    ok: bool = True
    codigo: str = ""
    detalle: str = ""
    aviso: str = ""
    tramos: list[str] = field(default_factory=list)
    rasgos: dict = field(default_factory=dict)

    def __bool__(self) -> bool:
        return self.ok

    def resumen(self) -> dict:
        """Lo que se guarda en los metadatos de la respuesta."""
        return {
            "bien_formada": self.ok,
            "motivo": self.codigo,
            "detalle": self.detalle,
            "tramos": self.tramos,
            "relacion": next((k[4:] for k in self.rasgos
                              if k.startswith("rel=") and self.rasgos[k]), ""),
            "conectiva": next((k[6:] for k in self.rasgos
                               if k.startswith("conec=") and self.rasgos[k]), ""),
        }


def revisar(consulta: str) -> Revision:
    """Mira la notación de una consulta: rasgos siempre, aviso casi nunca."""
    d = bien_formada(consulta)
    tramos = [t.texto for t in extraer(consulta)]
    r = Revision(ok=d.ok, tramos=tramos,
                 rasgos=rasgos_de_arbol(d.arbol if d.ok else None))
    r.rasgos["bien_formada"] = int(d.ok)
    r.rasgos["sin_notacion"] = int(d.arbol is None)
    if not d.ok:
        r.codigo = d.fallos[0] if d.fallos else ""
        r.detalle = d.detalle[0] if d.detalle else ""
        if r.codigo in MOTIVOS_QUE_SE_AVISAN and r.detalle:
            r.aviso = _TEXTO_AVISO % r.detalle
    return r
