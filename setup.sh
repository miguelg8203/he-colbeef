#!/bin/bash
# ── Setup HE Colbeef ──────────────────────────────────────────────────────────
echo "🔧 Instalando dependencias..."
cd backend
pip install -r requirements.txt

echo ""
echo "✅ Instalación completa."
echo ""
echo "▶️  Para iniciar el servidor:"
echo "   cd backend"
echo "   python main.py"
echo ""
echo "🌐 Luego abre: http://127.0.0.1:8000"
