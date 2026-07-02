[app]
title = Ficha de D&D
package.name = dndsheet
package.domain = org.suacampanha

source.dir = .
source.include_exts = py,kv,png,jpg,atlas
version = 1.0

requirements = python3,kivy

orientation = portrait
fullscreen = 0

# Descomente e adicione um icon.png (512x512) na raiz do projeto se quiser um ícone customizado
# icon.filename = %(source.dir)s/icon.png

android.permissions =

android.api = 33
android.minapi = 21
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
