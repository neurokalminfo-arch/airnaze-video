#!/usr/bin/env bash
# Entorno del estilo noche neón: pycairo, numpy, scipy, pillow + fuente Inter.
set -e
pip install --break-system-packages -q pycairo numpy scipy pillow 2>/dev/null || true
if ! fc-list | grep -q "Inter Display"; then
  mkdir -p ~/.fonts && cd /tmp && curl -sSL -o inter.zip https://github.com/rsms/inter/releases/download/v4.0/Inter-4.0.zip \
    && python3 -c "import zipfile;z=zipfile.ZipFile('inter.zip');[z.extract(n,'inter') for n in z.namelist() if n.endswith('.ttf') or n.endswith('.otf')]" \
    && find inter -name 'InterDisplay*.otf' -o -name 'InterDisplay*.ttf' | xargs -I{} cp {} ~/.fonts/ ; fc-cache -f >/dev/null
fi
fc-list | grep -q "Inter Display" && echo "listo (Inter Display ok)" || echo "AVISO: falta Inter Display"
