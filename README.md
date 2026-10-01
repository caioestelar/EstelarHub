# EstelarTemplate (STL-TEMPLATE)

## Estelar Hub Standalone (desenvolvimento)

O repositório agora também contém a camada de aplicativo standalone. No Windows com QGIS 4 instalado, execute `run_estelar_hub.bat`; ele inicializa PyQGIS em processo, sem abrir a janela principal do QGIS, e mostra o dashboard Estelar Hub. O módulo Mapa de Acesso continua compartilhando a janela e o fluxo de geração existentes.

Arquitetura, inicialização e limites atuais de empacotamento: [estelar_hub/README.md](estelar_hub/README.md). O `.bat` é o launcher de desenvolvimento; um instalador/`Estelar Hub.exe` distribuível exige empacotar o runtime QGIS/Qt/GDAL/PROJ e validar a redistribuição dessas dependências.

Plugin QGIS 3.x que substitui a macro de projeto `openProject` / `saveProject`
/ `closeProject` usada pela Estelar Engenharia para padronizar o Mapa de
Localização, os layouts de impressão, o SRC (SIRGAS 2000/UTM), o
município/UF e a área de estudo de cada empreendimento.

## Arquitetura

```
┌─────────────────────────────┐
│        __init__.py          │  classFactory() — ponto de entrada QGIS
└──────────────┬───────────────┘
               │
┌──────────────▼───────────────┐
│     estelar_template.py      │  Classe EstelarTemplate (initGui/run/unload)
│  - registra ação no toolbar  │
│  - inicia/para o timer       │
└──────────────┬───────────────┘
               │ run()
┌──────────────▼───────────────┐
│   ui/janela_projeto.py       │  QDialog JanelaProjeto (somente UI)
│  - widgets, eventos          │
└──────────────┬───────────────┘
               │ delega lógica
┌──────────────▼─────────────────────────────────────────────┐
│                          core/                              │
│  projeto.py   → orquestra: gerar_projeto(), resetar_template()│
│  preview.py   → desenhar_retangulos(), atualizar_preview()  │
│  kml.py       → importar_kml(), importar_kmz()              │
│  municipios.py→ descobrir_municipio(), descobrir_uf()       │
│  layouts.py   → renomear_layouts(), atualizar_layouts()     │
│  variaveis.py → salvar_variaveis(), carregar_variaveis()    │
│  recorte.py   → criar_area_estudo(), recortar_camadas()     │
└──────────────┬────────────────────────────────────────────┘
               │ usa
┌──────────────▼───────────────┐
│           utils/             │
│  constants.py → OBRAS, EPSG_ZONAS, nomes de camadas, etc.   │
│  helpers.py   → formatação de escala, transformação de pt.  │
└───────────────────────────────┘
```

## Árvore completa do projeto

```
EstelarTemplate/
├── __init__.py
├── metadata.txt
├── estelar_template.py
├── resources.qrc
├── resources.py
├── icon.png
├── README.md
├── i18n/                       (reservado para traduções .ts/.qm)
├── ui/
│   ├── __init__.py
│   ├── janela_projeto.py
│   └── assets/                 (reservado para ícones/imagens da UI)
├── core/
│   ├── __init__.py
│   ├── preview.py
│   ├── layouts.py
│   ├── variaveis.py
│   ├── municipios.py
│   ├── recorte.py
│   ├── kml.py
│   └── projeto.py
└── utils/
    ├── __init__.py
    ├── helpers.py
    └── constants.py
```

## Instalação no QGIS

1. Feche o QGIS.
2. Copie a pasta inteira `EstelarTemplate/` para o diretório de plugins do QGIS:
   - **Windows**: `C:\Users\<usuário>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\`
   - **Linux**: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - **macOS**: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
3. Abra o QGIS → menu **Complementos → Gerenciar e Instalar Complementos**.
4. Na aba **Instalados**, marque a caixa ao lado de **EstelarTemplate** para ativá-lo.
5. Um ícone "Templetizador STL" aparecerá na barra de ferramentas e no menu **Templetizador-Estelar**.

> Alternativa rápida para desenvolvimento: crie um link simbólico em vez de
> copiar a pasta, para poder editar o código-fonte no lugar de origem:
> ```
> ln -s /caminho/para/EstelarTemplate ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/EstelarTemplate
> ```

## Compilando o `resources.qrc`

O plugin **não depende** de `resources.py` para funcionar — o ícone da
barra de ferramentas é carregado por caminho de arquivo direto
(`os.path.join(self.plugin_dir, "icon.png")`). O `resources.qrc` foi
incluído para completude da estrutura e para permitir, futuramente, o uso
de ícones via URI Qt (`:/plugins/EstelarTemplate/...`) em vez de caminho
absoluto.

Para compilar, com o ambiente Python do QGIS ativo (o mesmo que tem o
PyQt5 usado pelo QGIS):

```bash
cd EstelarTemplate
pyrcc5 -o resources.py resources.qrc
```

No **OSGeo4W Shell** (Windows), o comando é o mesmo, desde que executado
dentro do shell que já tem `pyrcc5` no PATH. Se `pyrcc5` não for
encontrado, ele geralmente está em `C:\OSGeo4W\apps\Python3X\Scripts\`.

## Depurando o plugin no QGIS

1. Instale o plugin **Plugin Reloader** (via Gerenciador de Complementos) —
   ele permite recarregar o EstelarTemplate sem reiniciar o QGIS a cada
   alteração de código.
2. Abra o **Painel Python** do QGIS (menu **Complementos → Console Python**)
   para ver exceções e usar `print()`/`iface` interativamente.
3. Para depuração com breakpoints, use `debugpy`:
   ```python
   # no console Python do QGIS
   import debugpy
   debugpy.listen(5678)
   debugpy.wait_for_client()
   ```
   e conecte o VS Code (ou outra IDE) a `localhost:5678` com a configuração
   "Python: Attach".
4. Erros de execução do plugin (exceptions não tratadas fora dos blocos
   `try/except` já existentes) aparecem no **Log de Mensagens** do QGIS,
   aba "Python" — vale a pena deixá-lo aberto durante os testes.
5. Como toda a lógica de negócio está isolada em `core/` e `utils/`, com
   funções puras (sem depender de widgets), é possível testar boa parte
   dela fora do QGIS com stubs simples de `qgis.core`/`qgis.gui` — útil
   para testes automatizados de regressão.

## Problemas identificados na macro original e melhorias aplicadas

1. **Retângulo de preview (rb_500) nunca era usado como máscara real** —
   era puramente visual. Agora ele vira uma camada real `AREA_ESTUDO`
   (`core/recorte.py:criar_area_estudo`), usada para recortar rios,
   municípios e estradas, e disponível para futuras exportações.
2. **Recorte de rios por todo o polígono do estado** — extremamente caro
   para camadas grandes. Substituído por recorte pela `AREA_ESTUDO`
   (muito menor), com um `QgsSpatialIndex` para pré-filtrar candidatas
   antes do teste geométrico exato (`core/recorte.py:recortar_camadas`).
3. **`coord_x`/`coord_y` gravados no SRC de origem do KML**, mesmo depois
   do SRC do projeto mudar para UTM — variável ficava inconsistente com o
   resto do projeto. Corrigido: o ponto é reprojetado para o SRC final do
   projeto antes de salvar (`utils/helpers.py:transformar_ponto`).
4. **Bloco de limpeza de variáveis duplicado** em `resetar_template`
   (dois laços `for` idênticos em sequência) — unificado em
   `core/variaveis.py:limpar_variaveis`.
5. **`QgsExpressionContextUtils.setProjectVariable` para `tipo_projeto` e
   `zona_utm` chamados duas vezes seguidas** — eliminado.
6. **Timer periódico criado dentro do gatilho `closeProject()`** — nome
   semanticamente enganoso (o timer continuava rodando indefinidamente,
   inclusive depois do projeto fechar; nunca era parado — vazamento de
   recurso). Agora o timer é criado e iniciado em `initGui()` e
   devidamente parado em `unload()` (`estelar_template.py`).
7. **Atualização do preview por manipulação de índice de string**
   (`linhas[2]`, `linhas[3]`) — frágil: qualquer mudança no texto inicial
   quebraria silenciosamente a atualização. Substituído por um dicionário
   de estado (`dlg._preview_dados`) e uma função de renderização
   (`core/preview.py:montar_texto_preview`).
8. **Nenhuma validação de obra/arquivo antes de fechar o diálogo** — o
   usuário podia clicar em "GERAR PROJETO" com campos vazios e nada
   acontecia, sem nenhum aviso. Agora `JanelaProjeto.accept()` valida e
   exibe um aviso antes de fechar.
9. **Nenhum tratamento de erro** em toda a macro — qualquer exceção
   (arquivo inválido, camada ausente, etc.) interrompia a execução
   silenciosamente. Todas as operações críticas agora estão envolvidas em
   `try/except`, com `QMessageBox.critical` informando o usuário.
10. **Variável de projeto `area_estudo` armazenando a UF** — nome pouco
    claro (parece que deveria conter uma área/geometria de estudo, mas
    guarda a sigla da UF). Mantido por compatibilidade com layouts
    existentes, mas agora uma variável adicional `uf`, com nome correto,
    também é gravada.
11. **Hack de macro para registrar um botão "Recarregar STL" apenas uma
    vez** (`hasattr(iface, "_botao_stl_reload")`) — necessário apenas
    porque macros de projeto recarregam o script inteiro repetidamente.
    Como o plugin tem ciclo de vida próprio (`initGui`/`unload`), esse
    hack foi removido.
12. **E-mail de contato com domínio `.com.bt`** no cabeçalho original da
    macro — provavelmente um typo de `.com.br`. Corrigido em
    `metadata.txt` e nos cabeçalhos dos módulos (ajuste se o domínio
    `.bt` for intencional).

Todas essas correções foram validadas com testes de fumaça (mocks de
`qgis.core`/`qgis.gui`) que exercitam o fluxo completo: construção da UI,
carregamento de KML, cálculo de escala, geração do projeto, criação da
`AREA_ESTUDO`, recorte de camadas, reset de template e o timer periódico.
#   E s t e l a r M a p T o o l s 
 
 