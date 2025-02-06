import valeurs_modales, filaires, voiles, geo_hypo
import time
import pandas as pd
from numpy import set_printoptions

# Valeurs des résistances des Slabes ***** A COMPLETER AVEC LES VALEURS REELLES *****
resistance_slabe = {"SLABE8_Zs_initial": {"Fx_Rd": 110.88, "Fy_Rd": 46.55, "Fz_Rd": 30.10},
                    "SLABE8_Zs_final": {"Fx_Rd": 110.88, "Fy_Rd": 46.55, "Fz_Rd": 30.10},
                    "SLABE8_ZAs_initial": {"Fx_Rd": 55.44, "Fy_Rd": 33.10, "Fz_Rd": 23.06},
                    "SLABE8_ZAs_final": {"Fx_Rd": 55.44, "Fy_Rd": 33.10, "Fz_Rd": 23.06},
                    "SLABE8_ZZs_initial": {"Fx_Rd": 110.88, "Fy_Rd": 66.20, "Fz_Rd": 46.13},
                    "SLABE8_ZZs_final": {"Fx_Rd": 110.88, "Fy_Rd": 66.20, "Fz_Rd": 46.13},
                    "SLABE": {"Fx_Rd": 110.88, "Fy_Rd": 66.20, "Fz_Rd": 46.13}
                    }

# Valeurs du psi pour les différents modèles de Slabe  ***** A COMPLETER AVEC LES VALEURS REELLES *****
psi_slabe = {"SLABE_1": 0, "SLABE_2": 0, "SLABE_3": 0, "SLABE_4": 0}

# Paramètres pour visualiser les DataFrames en entier dans la console Python
desired_width = 600
pd.set_option('display.width', desired_width)
set_printoptions(linewidth=desired_width)
pd.set_option('display.max_columns', 50)
pd.set_option('display.max_rows', 10)



def get_pages_st(ndc, rupteur: bool):
    ndc = ndc.split(">>")
    if rupteur:
        pages = {'Geometrie': ndc[0],
                 'Hypotheses': ndc[1],
                 'Valeurs_modales': ndc[2],
                 'Efforts_filaires': ndc[3],
                 'Description_filaires': ndc[4],
                 'Torseurs_voiles': ndc[5],
                 'Coordonnées_voiles': ndc[6],
                 'Epaisseurs_voiles': ndc[7],
                 'Torseurs_etages_voiles': ndc[8],
                 }
    else:
        pages = {'Geometrie': ndc[0],
                 'Hypotheses': ndc[1],
                 'Valeurs_modales': ndc[2],
                 'Torseurs_voiles': ndc[4],
                 'Coordonnées_voiles': ndc[5],
                 'Epaisseurs_voiles': ndc[6],
                 'Torseurs_etages_voiles': ndc[7],
                 }
    return pages


def analyse_ndc(path_rupteur, path_base):
    # Initialisation chrono
    start = time.time()
    # Récupération des pages des 2 notes de calculs
    pages_rupt = get_pages_st(path=path_rupteur, rupteur=True)
    pages_base = get_pages_st(path=path_base,rupteur=False)
    # Analyse de la géométrie des modèles
    geo_hypo.analyse_geometrie(pages_rupt["Geometrie"], pages_base["Geometrie"])
    #Analyse des hypothèses des modèles
    geo_hypo.analyse_hypotheses(pages_rupt["Hypotheses"], pages_base["Hypotheses"])
    # Analyse des valeurs modales
    valeurs_modales.analyse_valeurs_modales(pages_rupt["Valeurs_modales"], pages_base["Valeurs_modales"])
    # Analyse des efforts dans les rupteurs
    filaires.analyse_efforts_rupteurs(pages_rupt["Efforts_filaires"], pages_rupt["Description_filaires"],
                                      resistance_slabe, gamma=1.3)
    # Vérification des coordonnées des voiles
    voiles.analyse_coord_voiles(pages_rupt["Coordonnées_voiles"], pages_base["Coordonnées_voiles"])
    # Analyse des efforts dans les voiles intérieurs
    voiles.analyse_efforts_voiles(pages_rupt['Torseurs_voiles'], pages_base["Torseurs_voiles"], ratio_limite=1.1)
    # Arrêt du chroo
    end = time.time()
    temps = round(end - start, 2)
    # Affichage du temps d'exécution


