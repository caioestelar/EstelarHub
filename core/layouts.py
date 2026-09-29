# -*- coding: utf-8 -*-
"""
core/layouts.py
================
Operações sobre o QgsLayoutManager: renomear os layouts de impressão com
o prefixo da obra atual, restaurar o prefixo neutro ("XXX-") ao resetar o
template, atualizar (refresh) todos os layouts periodicamente, e importar
os layouts QPT armazenados no servidor do template.
"""

import os

from qgis.PyQt.QtCore import QIODevice, QFile
from qgis.PyQt.QtXml import QDomDocument
from qgis.core import QgsLayoutItemMap, QgsPrintLayout, QgsProject, QgsReadWriteContext


def carregar_layout(nome_layout, caminho_qpt):
    """Carrega um layout QPT para o projeto, evitando duplicidade."""
    try:
        if not os.path.exists(caminho_qpt):
            print(f"[ESTELAR] Erro: Arquivo de layout não encontrado: {caminho_qpt}")
            return False

        gerenciador = QgsProject.instance().layoutManager()

        for layout_existente in gerenciador.printLayouts():
            if layout_existente.name() == nome_layout:
                print(f"[ESTELAR] Layout já existe: {nome_layout}")
                return False

        arquivo = QFile(caminho_qpt)
        modo_leitura = (
            QIODevice.OpenModeFlag.ReadOnly
            | QIODevice.OpenModeFlag.Text
        )
        if not arquivo.open(modo_leitura):
            raise OSError(arquivo.errorString())

        documento = QDomDocument()
        try:
            resultado = documento.setContent(arquivo)
        finally:
            arquivo.close()

        if isinstance(resultado, tuple):
            ok, mensagem, linha, coluna = resultado
            if not ok:
                raise ValueError(
                    f"XML inválido na linha {linha}, coluna {coluna}: {mensagem}"
                )
        elif not resultado:
            raise ValueError(f"Arquivo QPT inválido: {caminho_qpt}")

        layout = QgsPrintLayout(QgsProject.instance())
        layout.loadFromTemplate(documento, QgsReadWriteContext())
        layout.setName(nome_layout)

        for layout_existente in gerenciador.printLayouts():
            if layout_existente.name() == nome_layout:
                print(f"[ESTELAR] Layout já existe: {nome_layout}")
                return False

        gerenciador.addLayout(layout)
        print(f"[ESTELAR] Layout carregado: {nome_layout}")
        return True
    except Exception as e:
        print(f"[ESTELAR] Erro: {e}")
        raise RuntimeError(
            f"Falha ao importar o layout {nome_layout}: {e}"
        ) from e


def carregar_layouts_estelar():
    """Carrega os layouts QPT do template no momento da geração do projeto."""
    try:
        pasta_layouts = r"Q:\STL-TEMPLATE-QGIZ\BASES\LAYOUT"

        if not os.path.isdir(pasta_layouts):
            raise FileNotFoundError(
                f"Pasta de layouts não encontrada: {pasta_layouts}"
            )

        arquivos = sorted(
            arquivo for arquivo in os.listdir(pasta_layouts)
            if arquivo.lower().endswith(".qpt")
        )
        if not arquivos:
            raise FileNotFoundError(
                f"Nenhum arquivo QPT encontrado em: {pasta_layouts}"
            )

        gerenciador = QgsProject.instance().layoutManager()
        layouts_existentes = gerenciador.printLayouts()

        for arquivo in arquivos:
            caminho_qpt = os.path.join(pasta_layouts, arquivo)
            nome_layout = os.path.splitext(arquivo)[0]
            identificador = nome_layout.partition("-")[2]
            ja_carregado = any(
                layout.name() == nome_layout
                or layout.name().endswith(f"-{identificador}")
                for layout in layouts_existentes
            )
            if ja_carregado:
                continue

            if not carregar_layout(nome_layout, caminho_qpt):
                raise RuntimeError(f"Não foi possível carregar o layout: {arquivo}")
            layouts_existentes = gerenciador.printLayouts()
    except Exception as e:
        raise RuntimeError(f"Erro ao carregar os layouts do template: {e}") from e


def renomear_layouts(projeto: QgsProject, obra: str) -> None:
    """Troca o prefixo 'XXX-' pelo código da obra em todos os layouts.

    Ex: 'XXX-MAPA-LOCALIZACAO' -> 'STL-MAPA-LOCALIZACAO'
    """
    gerenciador = projeto.layoutManager()

    for layout in gerenciador.printLayouts():
        nome_atual = layout.name()

        if nome_atual.startswith("XXX-"):
            layout.setName(nome_atual.replace("XXX-", f"{obra}-", 1))


def aplicar_escalas_layouts(
    projeto: QgsProject,
    escalas: dict[str, int],
) -> None:
    """Aplica cada escala ao item de mapa do layout correspondente.

    O identificador 001, 002 ou 003 pode estar no nome do layout. Assim,
    a escala de um layout nunca sobrescreve a escala dos demais.
    """
    gerenciador = projeto.layoutManager()

    for chave, escala in escalas.items():
        if not escala:
            continue

        identificador = str(chave).zfill(3)
        layouts_correspondentes = [
            layout
            for layout in gerenciador.printLayouts()
            if identificador in layout.name()
        ]

        for layout in layouts_correspondentes:
            mapas = [
                item for item in layout.items()
                if isinstance(item, QgsLayoutItemMap)
            ]
            for mapa in mapas:
                mapa.setScale(float(escala))
            layout.refresh()


def restaurar_layouts(projeto: QgsProject) -> None:
    """Restaura o prefixo neutro 'XXX-' em todos os layouts, usado ao
    resetar o template. Reproduz a lógica original: mantém tudo depois do
    primeiro '-' e substitui apenas o prefixo.
    """
    gerenciador = projeto.layoutManager()

    for layout in gerenciador.printLayouts():
        partes = layout.name().split("-")

        if len(partes) >= 2:
            layout.setName("XXX-" + "-".join(partes[1:]))


def atualizar_layouts(projeto: QgsProject) -> None:
    """Força o refresh() de todos os layouts de impressão do projeto.

    Usado pelo timer periódico para manter os textos dinâmicos dos
    layouts (que dependem das variáveis de projeto e da tabela de
    coordenadas) sempre atualizados.
    """
    try:
        for layout in projeto.layoutManager().printLayouts():
            layout.refresh()
    except Exception:
        # Silencioso de propósito: essa função roda dentro de um timer
        # periódico e não deve interromper a experiência do usuário.
        pass
