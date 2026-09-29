# -*- coding: utf-8 -*-
"""
core/projeto.py
================
Módulo de orquestração. Contém a função `gerar_projeto()`, que reúne toda a
lógica que, na macro original, rodava depois de:

    dlg = JanelaProjeto()
    if not dlg.exec():
        return

Também contém a verificação de "obra já configurada" (antes de abrir a
janela), a rotina de reset do template, e a fábrica do timer periódico que
mantém a tabela de coordenadas e os layouts atualizados.

Nenhuma função aqui constrói widgets — toda interação com a UI (o
QDialog `JanelaProjeto`) é feita através de um objeto `dlg` já finalizado
(aceito pelo usuário), o que mantém a camada de UI e a lógica de negócio
desacopladas (ver ui/janela_projeto.py).
"""

from qgis.PyQt.QtCore import QTimer, Qt
from qgis.PyQt.QtWidgets import QApplication, QMessageBox, QProgressDialog
import os

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsProject,
    QgsVectorLayer,
)

from . import carregar_bases, kml, layouts, municipios, recorte, variaveis
from ..utils import constants, helpers


def obra_ja_configurada(projeto: QgsProject) -> bool:
    """Retorna True se já existe uma obra configurada no projeto atual
    (ou seja, se a variável 'obra' aponta para uma camada já carregada).
    """
    obra = helpers.obter_variavel_projeto(projeto, "obra")

    if not obra:
        return False

    return bool(projeto.mapLayersByName(obra))


def confirmar_reconfiguracao(parent=None) -> bool:
    """Pergunta ao usuário se deseja reconfigurar o STL-TEMPLATE quando já
    existe uma obra carregada. Retorna True se o usuário confirmar.
    """
    resposta = QMessageBox.question(
        parent,
        constants.NOME_PLUGIN,
        "Deseja reconfigurar o STL-TEMPLATE?\n\n"
        "Clique em SIM para alterar a usina, obra ou demais informações.",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    )
    return resposta == QMessageBox.StandardButton.Yes


def _atualizar_ponto_rotulo(projeto: QgsProject, centro) -> None:
    """Move o ponto da camada PONT_USINA_ROTULO para o centróide do
    empreendimento importado.
    """
    camadas = projeto.mapLayersByName(constants.LAYER_PONTO_ROTULO)

    if not camadas:
        return

    camada_usina = camadas[0]
    camada_usina.startEditing()

    try:
        feicao = next(camada_usina.getFeatures(), None)

        if feicao is not None:
            feicao.setGeometry(centro)
            camada_usina.updateFeature(feicao)
            camada_usina.commitChanges()
            camada_usina.triggerRepaint()
        else:
            camada_usina.rollBack()
    except Exception:
        camada_usina.rollBack()
        raise


def _atualizar_progresso(
    progresso: QProgressDialog,
    valor: int,
    mensagem: str,
    verificar_cancelamento: bool = False,
) -> None:
    progresso.setRange(0, 100)
    progresso.setLabelText(mensagem)
    progresso.setValue(valor)
    QApplication.processEvents()
    if verificar_cancelamento and progresso.wasCanceled():
        raise InterruptedError("Geração cancelada pelo usuário.")


def _callback_progresso_recorte(progresso, inicio: int, fim: int):
    def atualizar(indice: int, total: int, nome_camada: str) -> None:
        proporcao = indice / total if total else 1
        valor = inicio + round((fim - inicio) * proporcao)
        _atualizar_progresso(
            progresso, valor, f"Recortando camada: {nome_camada}..."
        )

    return atualizar


def gerar_projeto(dlg) -> bool:
    """Executa todo o fluxo de geração/configuração do projeto a partir dos
    dados preenchidos e confirmados na `JanelaProjeto`.

    Retorna True em caso de sucesso, False caso o usuário tenha deixado
    campos obrigatórios em branco (obra/arquivo) ou algum passo tenha
    falhado (nesse caso uma QMessageBox.critical já foi exibida).
    """
    projeto = QgsProject.instance()

    obra = dlg.cmb_obra.currentData() or dlg.cmb_obra.currentText().strip()
    tipo_projeto = dlg.cmb_tipo.currentText()
    zona_utm = dlg.cmb_zona.currentText()
    sigla_projetista = dlg.txt_sigla_projetista.text().strip()
    sigla_verificacao = dlg.txt_sigla_verificacao.text().strip()
    arquivo = dlg.arquivo
    pasta_projeto = dlg.txt_pasta_projeto.text().strip()

    if not obra:
        QMessageBox.warning(dlg, constants.NOME_PLUGIN, "Selecione o nome da obra antes de continuar.")
        return False

    if not arquivo:
        QMessageBox.warning(dlg, constants.NOME_PLUGIN, "Selecione um arquivo KML/KMZ antes de continuar.")
        return False

    if not os.path.isdir(pasta_projeto):
        QMessageBox.warning(dlg, constants.NOME_PLUGIN, "Selecione uma pasta válida para salvar o projeto.")
        return False

    progresso = None
    try:
        # 1) Copia as bases para a pasta do projeto e usa apenas as cópias.
        progresso = QProgressDialog(
            "Copiando as bases locais para o projeto...",
            "Cancelar cópia",
            0,
            0,
            dlg.parentWidget(),
        )
        progresso.setWindowTitle(constants.NOME_PLUGIN)
        progresso.setWindowModality(Qt.WindowModality.WindowModal)
        progresso.setMinimumDuration(0)
        progresso.setAutoClose(False)
        progresso.setAutoReset(False)
        progresso.show()
        _atualizar_progresso(
            progresso,
            0,
            "Copiando as bases locais para o projeto...",
            verificar_cancelamento=True,
        )
        pasta_bases = carregar_bases.copiar_bases_para_projeto(
            pasta_projeto, progresso
        )
        _atualizar_progresso(
            progresso,
            10,
            "Bases copiadas. Preparando o projeto...",
            verificar_cancelamento=True,
        )
        progresso.setCancelButton(None)

        _atualizar_progresso(progresso, 15, "Carregando as bases locais no projeto...")
        carregar_bases.carregar_bases_estelar(pasta_bases)

        # 2) Carrega os layouts do template e aplica o prefixo da obra.
        _atualizar_progresso(progresso, 30, "Carregando e configurando os layouts...")
        layouts.carregar_layouts_estelar()
        layouts.renomear_layouts(projeto, obra)

        # 3) Importa o KML/KMZ como camada definitiva do empreendimento.
        _atualizar_progresso(progresso, 40, "Importando o arquivo do empreendimento...")
        camada = kml.importar_camada(arquivo, obra)
        projeto.addMapLayer(camada)

        feicao = next(camada.getFeatures(), None)
        if feicao is None:
            raise ValueError("O arquivo selecionado não contém nenhuma feição.")

        geom = feicao.geometry()
        ponto_origem = geom.centroid().asPoint()

        # 3) Zona UTM automática, se aplicável.
        _atualizar_progresso(progresso, 52, "Calculando a localização do empreendimento...")
        if zona_utm == "AUTOMÁTICO":
            zona_utm = municipios.calcular_zona_utm(ponto_origem)

        # 4) Define o SRC do projeto de acordo com a zona UTM.
        epsg = municipios.obter_epsg_zona(zona_utm)
        if epsg:
            projeto.setCrs(QgsCoordinateReferenceSystem(epsg))

        # 5) Descobre município/UF automaticamente.
        _atualizar_progresso(progresso, 62, "Identificando município e UF...")
        municipio, uf = municipios.descobrir_municipio(projeto, geom)

        # 6) Calcula as escalas finais dos 3 layouts.
        _atualizar_progresso(progresso, 70, "Aplicando as escalas dos layouts...")
        escala_001 = helpers.calcular_escala(
            dlg.spin_001.value(), **_ref("001"))
        escala_002 = helpers.calcular_escala(
            dlg.spin_002.value(), **_ref("002"))
        escala_003 = helpers.calcular_escala(
            dlg.spin_003.value(), **_ref("003"))

        layouts.aplicar_escalas_layouts(
            projeto,
            {
                "001": escala_001,
                "002": escala_002,
                "003": escala_003,
            },
        )

        # 7) Corrige o ponto para o SRC final do projeto antes de salvar
        #    coord_x/coord_y (bug da macro original: gravava sempre no SRC
        #    de origem do KML, mesmo após o SRC do projeto mudar).
        ponto_projeto = helpers.transformar_ponto(ponto_origem, camada.crs(), projeto.crs())

        # 8) Salva as variáveis de projeto.
        variaveis.salvar_variaveis(
            projeto,
            obra=obra,
            tipo_projeto=tipo_projeto,
            zona_utm=zona_utm,
            sigla_projetista=sigla_projetista,
            sigla_verificacao=sigla_verificacao,
            escala_001=escala_001,
            escala_002=escala_002,
            escala_003=escala_003,
            municipio=municipio,
            uf=uf,
            coord_x=ponto_projeto.x(),
            coord_y=ponto_projeto.y(),
        )

        # 9) Cria a camada AREA_ESTUDO a partir do retângulo vermelho do
        #    preview (rb_500) e a usa como máscara para recorte de rios,
        #    municípios e estradas.
        if hasattr(dlg, "rb_500") and hasattr(dlg, "camada_preview"):
            _atualizar_progresso(progresso, 78, "Preparando a área de estudo...")
            geometria_area_estudo = dlg.rb_500.asGeometry()
            area_estudo = recorte.criar_area_estudo(
                projeto, geometria_area_estudo, dlg.camada_preview.crs()
            )

            recorte.recortar_camadas(
                projeto,
                area_estudo,
                constants.LAYERS_RIOS,
                _callback_progresso_recorte(progresso, 80, 84),
            )
            recorte.recortar_camadas(
                projeto,
                area_estudo,
                [constants.LAYER_MUNICIPIOS],
                _callback_progresso_recorte(progresso, 84, 86),
            )
            recorte.recortar_camadas(
                projeto,
                area_estudo,
                constants.LAYERS_ESTRADAS,
                _callback_progresso_recorte(progresso, 86, 92),
            )

        # 10) Move o ponto de rótulo da usina para o centróide do empreendimento.
        _atualizar_progresso(progresso, 94, "Salvando o projeto...")
        _atualizar_ponto_rotulo(projeto, geom.centroid())

        caminho_projeto = os.path.join(pasta_projeto, f"{obra}.qgz")
        projeto.setFileName(caminho_projeto)
        if not projeto.write():
            raise OSError(f"Não foi possível salvar o projeto em: {caminho_projeto}")

        _atualizar_progresso(progresso, 100, "Geração concluída.")
        progresso.close()
        QMessageBox.information(
            dlg, constants.NOME_PLUGIN,
            f"Projeto configurado e salvo em:\n{caminho_projeto}"
        )
        return True

    except InterruptedError:
        if progresso is not None:
            progresso.close()
        QMessageBox.information(
            dlg.parentWidget() or dlg,
            constants.NOME_PLUGIN,
            "Cópia cancelada. Arquivos já copiados podem permanecer na subpasta BASES.",
        )
        return False
    except Exception as erro:  # noqa: BLE001 - tratamento de erro amplo e intencional (req. 12)
        if progresso is not None:
            progresso.close()
        QMessageBox.critical(dlg, "Erro ao gerar projeto", str(erro))
        return False
    finally:
        if progresso is not None:
            progresso.close()


def _ref(chave: str) -> dict:
    """Pequeno adaptador entre o dicionário de constantes e a assinatura
    de `helpers.calcular_escala`.
    """
    dados = constants.ESCALAS_REFERENCIA[chave]
    return {
        "escala_referencia": dados["escala_referencia"],
        "largura_referencia": dados["largura_referencia"],
    }


def resetar_template(projeto: QgsProject) -> None:
    """Remove a camada da obra atual, limpa todas as variáveis de projeto,
    restaura os layouts para o prefixo neutro e retorna o SRC do projeto
    para o padrão (SIRGAS 2000 geográfico).

    Nenhuma confirmação é solicitada aqui: a UI é responsável por
    perguntar ao usuário antes de chamar esta função.
    """
    obra = helpers.obter_variavel_projeto(projeto, "obra")

    if obra:
        for camada in projeto.mapLayersByName(obra):
            projeto.removeMapLayer(camada.id())

    # Remove também a camada temporária de área de estudo, se existir.
    for camada in projeto.mapLayersByName(constants.AREA_ESTUDO_LAYER_NAME):
        projeto.removeMapLayer(camada.id())

    variaveis.limpar_variaveis(projeto)
    layouts.restaurar_layouts(projeto)

    projeto.setCrs(QgsCoordinateReferenceSystem(constants.SRC_PADRAO))


def criar_timer_atualizacao(intervalo_ms: int = constants.TIMER_INTERVALO_MS) -> QTimer:
    """Cria (sem iniciar) o QTimer responsável por atualizar periodicamente
    a camada de coordenadas das estruturas e os layouts de impressão.

    Na macro original esse timer era criado dentro de `closeProject()`,
    o que é semanticamente estranho (o gatilho de fechamento de projeto
    disparava um timer contínuo que nunca era parado, mesmo depois do
    projeto ser fechado — um vazamento de recurso). Aqui o ciclo de vida
    do timer é responsabilidade explícita do plugin principal
    (iniciado em `initGui`/`run`, parado em `unload`).
    """
    timer = QTimer()
    timer.timeout.connect(_atualizar_dados_periodicos)
    timer.setInterval(intervalo_ms)
    return timer


def _atualizar_dados_periodicos() -> None:
    projeto = QgsProject.instance()

    camadas = projeto.mapLayersByName(constants.LAYER_COORDENADAS)

    if camadas:
        camada: QgsVectorLayer = camadas[0]
        try:
            camada.reload()
            if camada.dataProvider():
                camada.dataProvider().forceReload()
            camada.triggerRepaint()
        except Exception:
            pass

    layouts.atualizar_layouts(projeto)
