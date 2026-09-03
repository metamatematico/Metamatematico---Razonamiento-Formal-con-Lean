# -*- coding: utf-8 -*-
"""Deja el traductor es→en listo en local, una sola vez.

POR QUE HACE FALTA UN PASO DE PREPARACION. `Helsinki-NLP/opus-mt-es-en` sólo
publica `pytorch_model.bin`, y transformers 5.x se niega a hacer `torch.load`
salvo con torch >= 2.6 (CVE-2025-32434). Aquí hay torch 2.5.1, y subirlo se
llevaría por delante el GNN entrenado y la compatibilidad con CUDA de este
entorno: no compensa por un traductor.

Así que se convierte una vez a safetensors, en un directorio local, y a partir
de ahí carga sin tocar `torch.load`. La conversión sí usa `torch.load`, pero
sobre un archivo que se acaba de descargar de un repositorio conocido y en un
paso manual y auditable, no en cada arranque.

POR QUE ES-EN Y NO AL REVES. Los alumnos preguntan en español. Todo lo demás
del sistema está en inglés: las 3 839 palabras clave del grafo, los 183 433
hechos de Mathlib, los ejemplos few-shot de miniF2F y el reconocedor de área.
Medido, el emparejador léxico se queda mudo en el 27 % de las consultas en
español y sólo en el 8,4 % de las de ProofNet, que son inglesas.

    python scripts/preparar_traductor.py
"""
import argparse
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8")

REPO = "Helsinki-NLP/opus-mt-es-en"
DESTINO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "traductor-es-en")

#: lo que hace falta para cargar el modelo sin el .bin
ACOMPAÑAN = ("config.json", "generation_config.json", "source.spm",
             "target.spm", "vocab.json", "tokenizer_config.json")


def main(a):
    import torch
    from huggingface_hub import hf_hub_download
    from safetensors.torch import save_file

    os.makedirs(DESTINO, exist_ok=True)
    for f in ACOMPAÑAN:
        try:
            shutil.copyfile(hf_hub_download(REPO, f),
                            os.path.join(DESTINO, f))
            print("  %s" % f)
        except Exception as exc:                  # noqa: BLE001
            print("  (sin %s: %s)" % (f, type(exc).__name__))

    binario = hf_hub_download(REPO, "pytorch_model.bin")
    # `weights_only=True`: no se ejecuta nada del pickle, sólo se leen tensores
    estado = torch.load(binario, map_location="cpu", weights_only=True)
    estado = {k: v for k, v in estado.items() if isinstance(v, torch.Tensor)}
    # safetensors no admite tensores que comparten memoria
    estado = {k: v.contiguous().clone() for k, v in estado.items()}
    save_file(estado, os.path.join(DESTINO, "model.safetensors"),
              metadata={"format": "pt"})
    mb = os.path.getsize(os.path.join(DESTINO, "model.safetensors")) / 1e6
    print("\n  -> %s (%.0f MB, %d tensores)" % (DESTINO, mb, len(estado)))

    if a.probar:
        from transformers import MarianMTModel, MarianTokenizer
        tok = MarianTokenizer.from_pretrained(DESTINO)
        mod = MarianMTModel.from_pretrained(DESTINO)
        T = ["Demuestra que un grupo de orden primo es cíclico",
             "¿Es 17 un número primo?",
             "¿De cuántas formas se pueden ordenar 5 libros?"]
        b = tok(T, return_tensors="pt", padding=True)
        o = mod.generate(**b, max_new_tokens=128)
        print()
        for x, y in zip(T, tok.batch_decode(o, skip_special_tokens=True)):
            print("  %-48s -> %s" % (x[:46], y))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--probar", action="store_true", default=True)
    sys.exit(main(ap.parse_args()))
