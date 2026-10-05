# -*- coding: utf-8 -*-
"""
utils/constants.py
===================
Constantes centrais do plugin EstelarTemplate.

Tudo o que antes estava "espalhado" dentro da macro (o dicionário de obras,
as siglas de zona UTM, os nomes de camadas mágicos usados em várias partes
do código, etc.) foi centralizado aqui. Isso resolve um dos maiores
problemas da macro original: strings literais repetidas (nomes de camadas,
nomes de variáveis de projeto) espalhadas por todo o arquivo, o que tornava
qualquer alteração arriscada (bastava errar a grafia em um lugar para
quebrar silenciosamente uma funcionalidade).
"""

# -----------------------------------------------------------------------
# Metadados de exibição
# -----------------------------------------------------------------------
NOME_PLUGIN = "EstelarMapTools"
RODAPE_TEXTO = "2026 @CHR - CAIO CHIARELLO ROCHA"

# -----------------------------------------------------------------------
# Dicionário de obras (sigla -> nome do empreendimento)
# Preservado exatamente como estava na macro original.
# -----------------------------------------------------------------------
OBRAS = {
    "STL": "ESTELAR ENG ASSOC",
    "EOM": "ESTELAR-O&M",
    "KDW": "KDW INCORPORADORA LTDA",
    "MTP": "MULTIPLA PARTICIPAÇÕES LTDA",
    "STI": "SUPORTE INCORPORADORA LTDA",
    "RAI": "COMPANHIA ENERG. URUGUAI - UHE IRAI",
    "CEG": "CELESC GERAÇÃO",
    "CCV": "PCH CAVEIRAS - CELESC",
    "PSE": "PONTE SERRADA GERAÇÃO DE ENERGIA",
    "AAL": "ALTO ALEGRE ENERGÉTICA S.A",
    "AMY": "ARROZEIRA MEYER",
    "ALF": "CGH ALTO FORTUNA",
    "ARZ": "PROYECTO ARAZATÍ",
    "AUR": "CGH AURORA",
    "BRE": "BOM RETIRO ENERGIA LTDA",
    "BVE": "BOA VISTA ENERGÉTICA SA",
    "CER": "CIA ENERG ENTRE RIOS - SAUDADE",
    "CBE": "CAMPO BELO ENERGÉTICA S.A",
    "CLP": "COSTA LESTE PARTICIPAÇÕES SA",
    "CDE": "PCH CONDE D'EU",
    "CEI": "CELULOSE IRANI",
    "CCE": "CONSTANZI ENERGIA LTDA",
    "CHM": "CHIMARRÃO ENERGÉTICA S.A",
    "CPN": "CIA PORTO NOVO DE ENERGIA",
    "CPZ": "CGH CHAPECOZINHO",
    "CGC": "CGC ENERGÉTICA",
    "CGR": "PCH CACHOEIRA GRANDE",
    "CPV": "PCH CAPIVARI",
    "CRZ": "CGH CRUZEIRO",
    "CXR": "PCH COXILHA RICA LTDA",
    "DOM": "AHE ANEL DE DOM MARCO",
    "DQE": "DUQUE ENERGÉTICA S.A",
    "EBV": "EÓLICA BOA VISTA ENERGIA SA",
    "ECN": "EÓLICA CALMON S.A.",
    "ESR": "CGH ESMERALDA",
    "ADC": "ADELINO CESCONETTO",
    "BTP": "CGH BARRA DO TIJUCO PRETO",
    "CDM": "CACHOEIRA DO MOINHO",
    "ESS": "CGHS ESPÍRITO SANTO",
    "FGV": "CGH FREI GALVÃO",
    "FRH": "CGH FREDERICO HEHR",
    "JCU": "INVENTÁRIO RIO JUCU",
    "MTC": "MONTE CASTELO",
    "NBL": "CGH NEBLINA",
    "PLO": "PILÕES",
    "SEP": "SÃO ESPERIDIÃO",
    "SLZ": "SÃO LUIZ",
    "SSO": "CGH SANSÃO",
    "TSS": "CGH THEODORO SCHWAMBACH SEGUNDO",
    "FLO": "FLORIPA ENERGÉTICA LTDA",
    "FPR": "FOZ DO PRATA ENERGÉTICA SA",
    "FRP": "FLORIPA ENERGÉTICA LTDA",
    "AGF": "CGH ÁGUA FRIA",
    "CBS": "CGH CACHOEIRA DO BISNAU",
    "GOA": "CGHS GOIÁS",
    "GOI": "GOIABEIRAS",
    "GUA": "CGH GUARÁ",
    "HIB": "HIB MONTES",
    "IGE": "ITUPORANGA GERAÇÃO DE ENERGIA LTDA",
    "ITR": "ITARARÉ ENERGÉTICA SA",
    "JBO": "PCH JAMBO",
    "KAZ": "KAZE ENERGÉTICA SA",
    "KEE": "KUMO ENERGIA EÓLICA SA",
    "LAC": "LACERDÓPOLIS ENERGÉTICA S.A",
    "LVT": "LAVA TUDO MONTANTE",
    "URU": "PCH URUPEMA",
    "LVJ": "LAVA TUDO JUSANTE",
    "BNN": "PCH BANANEIRAS",
    "LTD": "PCH LAVA TUDO",
    "SCR": "PCH SANTA CRUZ",
    "BAR": "BARRINHA",
    "LAM": "LAMBARI",
    "MAU": "MAUÊ",
    "MLU": "MEIA LUA",
    "MBC": "CGH MAMBUCA",
    "CTJ": "CGH CATUJI",
    "EBS": "CGH ESTÂNCIA BASSARGADA",
    "FCR": "CGH FAZENDA CRISÓLITA",
    "FSC": "CGH FAZENDA SANTA CRUZ",
    "MCR": "RIO MUCURI",
    "MNH": "CGH MARANHÃO",
    "SBA": "CGH SANTA BÁRBARA",
    "MEE": "MARMELEIRO ENERGIA EÓLICA",
    "MET": "PCH ESTRIBO",
    "MVS": "PCH VASSOURAS",
    "CDA": "PCH CACHOEIRA DAS ALMAS",
    "CRP": "PCH CARRAPATOS",
    "GML": "PCH GRÃO MOGOL",
    "MG5": "MG5 ENERGÉTICA LTDA",
    "MLV": "PCH MELO VIANA",
    "NEH": "PCH NOVA ERECHIM",
    "NVP": "PCH NOVA PRATA",
    "OUR": "PCH OURO",
    "BJE": "PCH BOM JESUS",
    "GMO": "UHE GUARDA MÓR",
    "PEL": "PCH PELOTAS",
    "PLT": "RIO PELOTAS",
    "SJO": "PCH SÃO JOÃO",
    "SVI": "PCH SANTA VITÓRIA",
    "TRO": "UHE TROPEIROS",
    "PNE": "PRESIDENTE NEREU",
    "PNH": "PINHEIRO ENERGÉTICA SA",
    "PRN": "PARANISA",
    "BVT": "PCH BELA VISTA",
    "CSM": "PCH CÓRREGO SANTA MARIA",
    "FAL": "PCH FALCÃO",
    "PRT": "RIO PRETO",
    "RON": "PCH RIBEIRÃO DA ONÇA",
    "ZEL": "PCH ZELINDA",
    "RCG": "RIO CÁGADO",
    "SDS": "CGH SAUDADES",
    "SJR": "CGH SÃO JERÔNIMO",
    "RAT": "RIO DAS ANTAS",
    "APA": "CGH APARECIDA",
    "BEU": "CGH BARRA DA EUROPA",
    "COR": "PCH CORAÇÃO",
    "RBB": "RIO BURRO BRANCO",
    "RCR": "RIO CARREIRO",
    "RDO": "PCH RODEIO",
    "IMB": "CGH IMBÉ",
    "RDJ": "USINAS RIO DE JANEIRO",
    "CTT": "CGH CATETE",
    "RGN": "PCH RIO GRANDINA",
    "VDN": "CGH VÉU DA NOIVA",
    "XVR": "PCH XAVIER",
    "RAP": "PCH RAPOSO",
    "AGS": "PCH ÁGUAS DA SERRA",
    "CEN": "CGH CENTRAL",
    "RBE": "RIO BENEDITO",
    "RME": "RIO MINAS ENERGIA S.A",
    "SAB": "ENERGÉTICA SABIÁ LTDA",
    "SDR": "SINVAL DORNELLA ENERGIA S.A",
    "SAM": "CGH SAMIX",
    "SAL": "PCH SALTINHO",
    "SAK": "SAKURA ENERGÉTICA S.A",
    "SAP": "SANTO ANTONIO DO PINHAL",
    "SCA": "STATKRAFT - PCH CANOAS",
    "STX": "CGH SANTO EXPEDITO",
    "STT": "UHE SANTA TEREZA",
    "SUL": "SUL ENERGIA S.A",
    "TCT": "PCHS TOCANTINS",
    "SMR": "PCH SAMARON",
    "ZCS": "PCH ZACARIAS",
    "UNI": "ENERGÉTICA UNIÃO S.A",
    "VOC": "VOTORANTIM - INSPEÇÃO CONDUTOS",
    "VST": "VOTORANTIM - CGH SANTANA",
    "XAX": "XAXIM ENERGÉTICA SA",
    "DIM": "DIM ENERGIA RENOVÁVEL S.A",
    "BUR": "BURANA ENERGIA S.A",
    "ENG": "CONSULTORIAS E PRÉ-PROJETOS",
    "EOL": "EÓLICAS",
    "UFV": "FOTOVOLTAICAS",
    "SEG": "SEGURANÇA DE BARRAGEM",
    "SER": "SERRANA ENGENHARIA",
    "BRG": "BROOKFIELD - GEOLOGIA",
    "TRC": "TRIÂNGULO - COMPLEXO TOROPI-GUASSUPI",
    "CCG": "CONSÓRCIO CANDONGA - GEOLOGIA",
    "PTN": "AIBH RIO PELOTINHAS",
    "JSP": "PCH JASP",
    "BSN": "BISNAU COMPLEXO FOTOVOLTAICO",
    "CAE": "CAITETU ENERGIA S.A",
    "CME": "CALAZANS MACHADO ENERGIA RENOVÁVEL S.A",
    "FLN": "FLORIPA ENERGIA S.A",
    "IMP": "IMPERATRIZ DA CONCEIÇÃO",
    "MON": "MONJOLO ENERGIA S.A",
    "PDT": "PEDESTAL ENERGÉTICA S.A",
    "PTE": "PERITORÓ ENERGIA S.A",
    "PCS": "PRINCESINHA DO SERIDÓ",
    "PCA": "PRINCESA DO AGRESTE",
    "RAS": "RAINHA DO SERTÃO",
    "TRN": "UFV TRINA",
    "TCM": "UFV TUCUM",
    "VLR": "VILA RICA ENERGIA S.A",
}

# -----------------------------------------------------------------------
# Tipos de projeto
# -----------------------------------------------------------------------
TIPOS_PROJETO = ["PCH", "UHE", "CGH", "EQL", "UFV", "OUTRO"]

# -----------------------------------------------------------------------
# Zonas UTM (SIRGAS 2000) disponíveis no combo
# -----------------------------------------------------------------------
ZONAS_UTM = [
    "AUTOMÁTICO",
    "18N", "19N", "20N", "21N", "22N", "23N", "24N", "25N",
    "18S", "19S", "20S", "21S", "22S", "23S", "24S", "25S",
]

# Códigos EPSG (SIRGAS 2000 / UTM) para cada zona.
EPSG_ZONAS = {
    "18N": "EPSG:31972",
    "19N": "EPSG:31973",
    "20N": "EPSG:31974",
    "21N": "EPSG:31975",
    "22N": "EPSG:31976",
    "18S": "EPSG:31978",
    "19S": "EPSG:31979",
    "20S": "EPSG:31980",
    "21S": "EPSG:31981",
    "22S": "EPSG:31982",
    "23S": "EPSG:31983",
    "24S": "EPSG:31984",
    "25S": "EPSG:31985",
}

# SRC padrão do projeto "zerado" (SIRGAS 2000 geográfico).
SRC_PADRAO = "EPSG:4674"

# -----------------------------------------------------------------------
# Retângulos de preview (vermelho / azul / verde)
# -----------------------------------------------------------------------
# Proporção largura/altura usada para desenhar os 3 retângulos de preview.
PROPORCAO_RETANGULO = 1.1946

# Cada layout tem uma escala de referência: quando a largura do retângulo
# é igual a `largura_referencia`, a escala exibida é `escala_referencia`.
# (escala_final = escala_referencia * largura_atual / largura_referencia)
ESCALAS_REFERENCIA = {
    "001": {"cor": "red", "escala_referencia": 500000, "largura_referencia": 2.5, "passo": 0.10},
    "002": {"cor": "blue", "escala_referencia": 100000, "largura_referencia": 1.0, "passo": 0.10},
    "003": {"cor": "green", "escala_referencia": 25000, "largura_referencia": 0.3, "passo": 0.05},
}

# -----------------------------------------------------------------------
# Nomes de camadas de referência do projeto (evita strings "mágicas"
# espalhadas pelo código, que era um dos maiores riscos da macro original).
# -----------------------------------------------------------------------
LAYER_MUNICIPIOS = "MUNICIPIOS_BRASIL"
LAYER_DEFINIR_AREA = "DEFINIR_ÁREA"
LAYER_PONTO_ROTULO = "PONT_USINA_ROTULO"
LAYER_COORDENADAS = "coordenadas_das_estruturas"

# Camadas de rios recortadas com base na área de estudo.
LAYERS_RIOS = ["RIOS_SEC.", "RIOS_PRINC.", "RIOS_TERC."]

# Camadas de estradas recortadas com base na área de estudo (extensível:
# basta adicionar o nome da camada de estradas usada no projeto).
LAYERS_ESTRADAS = ["ESTRADAS"]

# Nome da camada temporária de máscara criada a partir do retângulo
# vermelho (rb_500) do preview. Substitui o uso do QgsRubberBand como
# "geometria final" (ver core/recorte.py).
AREA_ESTUDO_LAYER_NAME = "AREA_ESTUDO"

# Bases de mapa usadas no preview do empreendimento.
URL_MAPA_BASE = (
    "type=xyz&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png"
)

URL_SATELITE = (
    "type=xyz&url=https://server.arcgisonline.com/"
    "ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
)

URL_SEM_CIDADES = (
    "type=xyz&url=http://:basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"
)

# -----------------------------------------------------------------------
# Variáveis de projeto gerenciadas pelo plugin
# -----------------------------------------------------------------------
VARIAVEIS_PROJETO = [
    "obra",
    "tipo_projeto",
    "zona_utm",
    "sigla_projetista",
    "sigla_verificacao",
    "layout_001",
    "layout_002",
    "layout_003",
    "municipio",
    "area_estudo",  # mantido por compatibilidade: historicamente guarda a UF
    "uf",
    "coord_x",
    "coord_y",
]

# -----------------------------------------------------------------------
# Timer de atualização automática (tabela de coordenadas + layouts)
# -----------------------------------------------------------------------
TIMER_INTERVALO_MS = 5000
