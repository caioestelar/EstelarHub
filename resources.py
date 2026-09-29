# -*- coding: utf-8 -*-
"""
resources.py
============
Este arquivo é o resultado da compilação de `resources.qrc` pelo utilitário
`pyrcc5` (PyQt5) e precisa ser GERADO na máquina/ambiente de desenvolvimento,
pois o binário depende da versão exata do PyQt5 instalada com o QGIS.

Este placeholder existe apenas para manter a estrutura de pastas completa
e documentar o comando de geração (ver README.md, seção "Compilando o
resources.qrc"). O plugin NÃO depende deste arquivo para funcionar: o
ícone da barra de ferramentas é carregado por caminho de arquivo direto em
`estelar_template.py` (`os.path.join(self.plugin_dir, "icon.png")`).

Para gerar a versão real e compilada deste arquivo, execute no diretório
do plugin:

    pyrcc5 -o resources.py resources.qrc

Depois de gerado, este arquivo passa a exportar os recursos Qt sob o
prefixo ":/plugins/EstelarTemplate/icon.png", permitindo usos como:

    QIcon(":/plugins/EstelarTemplate/icon.png")

em qualquer parte do plugin, sem depender de caminhos absolutos em disco.
"""
