# -*- coding: utf-8 -*-
"""
/***************************************************************************
 EstelarTemplate
                                 A QGIS plugin
 Este plugin automatiza processos para padronizar os desenhos da Estelar
                             -------------------
        begin                : 2026-09-23
        copyright            : (C) 2026 by CaioChiarello/ESTELAR ENGENHARIA ASSOCIADOS
        email                : caio@estelarengenharia.com.br
 ***************************************************************************/

 This script initializes the plugin, making it known to QGIS.
"""

__author__ = "CaioChiarello/ESTELAR ENGENHARIA ASSOCIADOS"
__date__ = "2026-09-23"
__copyright__ = "(C) 2026 by CaioChiarello/ESTELAR ENGENHARIA ASSOCIADOS"


def classFactory(iface):
    """Load EstelarTemplate class from file EstelarTemplate.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from .estelar_template import EstelarTemplate

    return EstelarTemplate(iface)
