# Ficha Portátil de D&D

App em Python (Kivy) para criar e manter fichas de personagem de D&D no
celular. Conforme a campanha avança, você edita a ficha diretamente e
registra cada mudança relevante em um histórico com data/hora.

## O que o app faz

- Lista de personagens salvos, com criação e exclusão.
- Ficha completa: raça, classe, subclasse, antecedente, nível, os 6
  atributos (com modificador calculado automaticamente), CA, PV
  (atual/máximo/temporário), deslocamento, iniciativa e bônus de
  proficiência.
- Botões rápidos de **dano** e **cura** que já descontam PV temporário
  primeiro e nunca deixam o PV passar do máximo ou ficar negativo.
- Lista de ataques (nome, bônus, dano) e de inventário, editáveis.
- Campo livre para traços de classe/talentos, recursos com uso limitado
  (ex.: "Fúria 2/3") e anotações de personalidade.
- **Histórico da campanha**: cada alteração importante fica registrada
  com data e hora, então dá pra ver a evolução do personagem sessão a
  sessão.
- Tudo salvo localmente em JSON (um arquivo por personagem), sem
  precisar de internet.

## Estrutura do projeto

```
dnd_sheet_app/
├── main.py          # App Kivy: telas e lógica de interface
├── sheet.kv          # Layout visual (Kivy language)
├── models.py          # Modelo de dados do personagem (puro Python, sem Kivy)
├── storage.py          # Salvar/carregar fichas em JSON
├── buildozer.spec       # Configuração para gerar o APK Android
├── requirements.txt
└── characters/          # (criado automaticamente) fichas salvas ao testar no desktop
```

`models.py` e `storage.py` não dependem do Kivy — dá para testá-los
direto com `python3` antes de mexer na interface.

## Rodando no computador para testar

Antes de gerar o APK, teste no desktop — é bem mais rápido de iterar:

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install kivy
python main.py
```

Uma janela vai abrir com o app rodando. As fichas ficam salvas em uma
pasta de dados do usuário (no Linux normalmente algo como
`~/.local/share/dndsheet/characters/`).

## Gerando o APK sem instalar nada (recomendado)

Este projeto já vem com um workflow do **GitHub Actions**
(`.github/workflows/build-apk.yml`) que compila o APK automaticamente
nos servidores do GitHub — de graça, sem precisar instalar Android
SDK/NDK na sua máquina.

Passo a passo:

1. Crie uma conta no [github.com](https://github.com) (se ainda não tiver).
2. Crie um repositório novo (pode ser privado), por exemplo `ficha-dnd-app`.
3. Suba a pasta `dnd_sheet_app` inteira para esse repositório. Pelo site
   mesmo dá pra fazer: abra o repositório → "Add file" → "Upload files"
   → arraste todos os arquivos e pastas (incluindo a pasta oculta
   `.github`) → "Commit changes" (direto no branch `main`).
4. Vá na aba **Actions** do repositório. Um workflow chamado
   "Build APK" deve começar a rodar sozinho (leva uns 10-20 minutos na
   primeira vez, porque baixa o Android SDK/NDK).
5. Quando terminar (bolinha verde ✅), clique no run finalizado → role
   até **Artifacts** → baixe `ficha-dnd-apk`. Dentro tem o `.apk`.
6. Transfira o `.apk` para o celular (Google Drive, cabo USB, etc.) e
   instale. O Android vai pedir para habilitar "instalar de fontes
   desconhecidas" — é normal para apps fora da Play Store.

Se o build falhar, a aba Actions mostra o log completo do erro — copie
a mensagem e me mande que eu ajusto o `buildozer.spec` ou o código.

## Gerando o APK localmente (alternativa)

Isso precisa ser feito em **Linux** (nativo, WSL, ou uma VM) — o
Buildozer não empacota para Android a partir do Windows/Mac
diretamente.

```bash
pip install buildozer cython
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf \
    libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev \
    libtinfo5 cmake libffi-dev libssl-dev

cd dnd_sheet_app
buildozer android debug
```

Na primeira execução, o Buildozer baixa sozinho o Android SDK/NDK
(pode demorar bastante). Ao final, o APK aparece em
`bin/dndsheet-1.0-arm64-v8a_armeabi-v7a-debug.apk`. Copie esse arquivo
para o celular e instale (pode ser preciso habilitar "instalar de
fontes desconhecidas" nas configurações do Android).

Para reinstalar direto via USB com o celular em modo desenvolvedor:

```bash
buildozer android debug deploy run
```

## Adicionar um ícone (opcional)

Coloque uma imagem quadrada (ex. 512x512) em `icon.png` na raiz do
projeto — o `buildozer.spec` já está configurado para usá-la.

## Por que os dados ficam só no celular

Por padrão o app não usa nenhum servidor — tudo é salvo localmente em
JSON. Isso significa que não há conta, login nem sincronização entre
aparelhos. Se no futuro você quiser sincronizar entre celular e
computador (por exemplo, via Google Drive ou um backend próprio), a
separação entre `models.py`/`storage.py` (dados) e `main.py`/`sheet.kv`
(interface) foi pensada exatamente para isso: dá pra trocar a forma de
salvar sem mexer na tela.

## Extensões fáceis de fazer depois

- Múltiplas fichas por "campanha" (agrupar personagens por pasta).
- Exportar uma ficha como PDF para imprimir.
- Botão de "long/short rest" que recupera recursos automaticamente.
- Rolagem de dados integrada (d20, ataques) usando o módulo `random`.
