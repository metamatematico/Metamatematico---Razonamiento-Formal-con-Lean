#!/bin/bash
# ══════════════════════════════════════════════════════════════════════
# setup_huggingface.sh — Deploy en Hugging Face Spaces (sin Lean)
# Gratis · 16 GB RAM · GPU T4 opcional
#
# Prerrequisito: tener cuenta en huggingface.co
# Uso: bash deploy/setup_huggingface.sh
# ══════════════════════════════════════════════════════════════════════

echo "╔══════════════════════════════════════════════╗"
echo "║   METAMATEMÁTICO — HuggingFace Spaces        ║"
echo "╚══════════════════════════════════════════════╝"

# Instalar huggingface_hub si no está
pip install huggingface_hub -q

echo ""
echo "Pasos para publicar en HuggingFace Spaces:"
echo ""
echo "1. Crear Space en https://huggingface.co/new-space"
echo "   - Owner: tu usuario"
echo "   - Space name: metamatematico"
echo "   - SDK: Docker"
echo "   - Hardware: CPU Basic (gratis) o T4 GPU (\$0.60/hora)"
echo ""
echo "2. Agrega el Space como remote:"
echo "   git remote add hf https://huggingface.co/spaces/TU_USUARIO/metamatematico"
echo ""
echo "3. Push:"
echo "   git push hf main"
echo ""
echo "4. Configurar secrets en HuggingFace:"
echo "   → Settings → Variables and secrets"
echo "   → Agregar: ANTHROPIC_API_KEY, GOOGLE_API_KEY, GROQ_API_KEY"
echo ""
echo "Nota: en HuggingFace Spaces el sistema funciona sin Lean 4"
echo "(verificación formal deshabilitada, resto del sistema 100% activo)"
