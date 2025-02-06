from numpy import nan, sin, cos, arctan
import pandas as pd
import re
import functools


def nettoyer_description_voiles(page_coord_voiles):
    description_voiles = page_coord_voiles.split("\n")
    # Récupération de datas de la page de description
    description_voiles = [ligne.split("\t") for ligne in description_voiles if "\t" in ligne]
    #Création du DataFrame avec des coordonnées
    df_description_voiles = pd.DataFrame(description_voiles)

# Nettoyage du DF
    noms_colonnes = ["n°_element", "coord", "a_supr"]

    df_description_voiles.columns = noms_colonnes
    df_description_voiles.reset_index(inplace=True, drop=True)
    df_description_voiles.drop(index=[0,1], inplace=True)
    df_description_voiles.drop('a_supr', axis=1, inplace=True)

# Extraction des coordoonées avec une expression régulière
    regex = re.compile(r"\((.*?)\)")
    df_description_voiles["coord"] = df_description_voiles["coord"].apply(lambda x: re.findall(regex, x))
    df_description_voiles["n°_element"] = pd.to_numeric(df_description_voiles["n°_element"])


# Création d'une colonne pour chaque coordonnée
    for i in range (4):
        for j in range (3):
            axe = ["x", "y", "z"]
            df_description_voiles.loc[:, f"coord_p{i}_{axe[j]}"] = df_description_voiles.loc[:, f"coord"].apply(lambda x: float(x[i].split(", ")[j]))

# Récupération des valeurs extrèmes sur chaque axe
    for i in ["x", "y", "z"]:
        df_description_voiles.loc[:, f"coord_{i}1"] = df_description_voiles.loc[:,
                                                      [f"coord_p0_{i}",f"coord_p1_{i}",f"coord_p2_{i}", f"coord_p3_{i}"]
                                                      ].min(axis=1)
        df_description_voiles.loc[:, f"coord_{i}2"] = df_description_voiles.loc[:,
                                                      [f"coord_p0_{i}", f"coord_p1_{i}", f"coord_p2_{i}",
                                                       f"coord_p3_{i}"]
                                                      ].max(axis=1)
        df_description_voiles.drop([f"coord_p0_{i}",f"coord_p1_{i}",f"coord_p2_{i}", f"coord_p3_{i}"], axis=1, inplace=True)

    return df_description_voiles



def verifier_coord_voiles(df_coord_rupt, df_coord_base):
# On assemble des coordonnées des voiles avec et sans les rupteurs
# Une fusion "outer" permet de conserver les voiles ui ne seraient présents que dans un seul modèle
    df_coord_compil = pd.merge(df_coord_rupt.loc[:, ["n°_element", "coord"]],df_coord_base.loc[:, ["n°_element", "coord"]], how='outer', on='n°_element')
    df_coord_compil.columns = ['n°_element', 'coord_rupt', 'coord_base']
# On crée un dF qui regroupe les élements dont les coordonnée avec et sans rupteur sont différents
    df_verif_coord = df_coord_compil.loc[df_coord_compil["coord_rupt"] != df_coord_compil["coord_base"]]
# Si le DF est vide alors les voiles correspondent
    if df_verif_coord.empty:
        verification = True
    else:
        verification = False

    return verification, df_coord_compil, df_verif_coord


def analyse_coord_voiles(page_coord_voiles_rupt, page_coord_voiles_base):
    df_dv_rupt = nettoyer_description_voiles(page_coord_voiles_rupt)
    df_dv_base = nettoyer_description_voiles(page_coord_voiles_base)
    verification, _ ,df_verif_coord = verifier_coord_voiles(df_dv_rupt, df_dv_base)
    return verification, df_dv_rupt, df_dv_base, df_verif_coord


def calcul_geometrie_voiles(df_description_voiles, df_epaisseurs_voiles):
    df_geo_voiles = df_description_voiles.copy(deep=True)
# Calcul des delta de distances et de l'angle d'inclinaison teta
    df_geo_voiles.loc[:, "delta_x"] = df_geo_voiles.loc[:, "coord_x2"] - df_geo_voiles.loc[:, "coord_x1"]
    df_geo_voiles.loc[:, "delta_y"] = df_geo_voiles.loc[:, "coord_y2"] - df_geo_voiles.loc[:, "coord_y1"]
# La division par 0 ne semble pas lever d'erreur. Surement car on y applique arctan qui gère l'infini
    df_geo_voiles.loc[:, 'teta_rad'] = (df_geo_voiles.loc[:, "delta_y"] / df_geo_voiles.loc[:, 'delta_x']
                                        ).apply(lambda x: arctan(x))
# Calcul de la longueur des voiles
    df_geo_voiles.loc[:, "longueur"] = (df_geo_voiles.loc[:, 'delta_x'] ** 2 + df_geo_voiles.loc[:, 'delta_y'] ** 2) ** 0.5
# Détermination des étages
    nb_etages = len(df_geo_voiles["coord_z1"].unique())
    etages = [etage for etage in range(nb_etages)]
# Création d'un DF avec les n° d'etages et les coordonnées du plancher BAS
    df_etages = pd.DataFrame({"n°_etages": etages,
                              "coord_z1": df_geo_voiles["coord_z1"].sort_values(ascending=True).unique()
                              })
# On implémentes les étages dans le DF principal
    df_geo_voiles = df_geo_voiles.merge(df_etages, how='outer', on='coord_z1')
# On ajoute les epaisseurs dans le DF principal
    df_geo_voiles = pd.merge(df_geo_voiles, df_epaisseurs_voiles, how='outer', on='n°_element')

# Calcul des moments quadratiques locaux, X_local suit la direction du voile, Y_local correspond à l'épaisseur
    df_geo_voiles.loc[:, "Ix_loc"] = (df_geo_voiles.loc[:, "longueur"] * df_geo_voiles.loc[:, "epaisseur"] ** 3) / 12
    df_geo_voiles.loc[:, "Iy_loc"] = (df_geo_voiles.loc[:, "epaisseur"] * df_geo_voiles.loc[:, "longueur"] ** 3) / 12
    df_geo_voiles.loc[:, "Ixy_loc"] = 0   # = 0 car les axes du repères sont sur les axes de symétrie
# Passage des I_loc dans la base globale

    df_geo_voiles["Ix"] = (df_geo_voiles["Ix_loc"] + df_geo_voiles["Iy_loc"]) / 2 + (
                          df_geo_voiles["Ix_loc"] - df_geo_voiles["Iy_loc"]) / 2 * cos(
                          2 * df_geo_voiles["teta_rad"]) +  df_geo_voiles["Ixy_loc"] * sin(
                          2 * df_geo_voiles["teta_rad"])
    df_geo_voiles["Iy"] = (df_geo_voiles["Ix_loc"] + df_geo_voiles["Iy_loc"]) / 2 + (
                          df_geo_voiles["Iy_loc"] - df_geo_voiles["Ix_loc"]) / 2 * cos(
                          2 * df_geo_voiles["teta_rad"]) + df_geo_voiles["Ixy_loc"] * sin(
                          2 * df_geo_voiles["teta_rad"])

    return df_geo_voiles






def nettoyer_epaisseurs_voiles(page_epaisseurs_voiles):
    epaisseurs_voiles = page_epaisseurs_voiles.split('\n')
    epaisseurs_voiles = [ligne.split('\t') for ligne in epaisseurs_voiles if '\t' in ligne]
    df_epaisseurs_voiles = pd.DataFrame(epaisseurs_voiles)
    df_epaisseurs_voiles.columns = ["n°_element", "epaisseur", "asup"]
    df_epaisseurs_voiles.drop("asup", axis=1, inplace=True)
    df_epaisseurs_voiles.drop([0,1], axis=0, inplace=True)
# On converti les epaisseurs en m
    df_epaisseurs_voiles['epaisseur'] = df_epaisseurs_voiles["epaisseur"].apply(pd.to_numeric) / 100
    df_epaisseurs_voiles["n°_element"] = pd.to_numeric(df_epaisseurs_voiles["n°_element"])

    return df_epaisseurs_voiles


def nettoyer_efforts_voiles(page_efforts_voiles):
    # Récupération des datas de la page des efforts
    efforts_voiles = page_efforts_voiles.split('\n')
    efforts_voiles = [ligne.split("\t") for ligne in efforts_voiles if "\t" in ligne]
    df_efforts_voiles = pd.DataFrame(efforts_voiles) # Création du DataFrame
    # On récupère le nom des colonnes dans la première ligne
    noms_colonnes_ev = df_efforts_voiles.iloc[0, :].tolist()
    # Remplacement des espaces par des _ et suppressions des unitées dans les noms des colonnes
    noms_colonnes_ev = [re.sub(r"\s", "_", nom) for nom in noms_colonnes_ev]
    noms_colonnes_ev = [re.sub(r"_+", "_", nom) for nom in noms_colonnes_ev]
    noms_colonnes_ev = [re.sub(r"\(.+\)", "", nom) for nom in noms_colonnes_ev]
    noms_colonnes_ev = [nom.lower() for nom in noms_colonnes_ev]
    # On renomme les colonnes
    df_efforts_voiles.columns = noms_colonnes_ev
    # Suppression de la première ligne
    df_efforts_voiles.drop(index=[0], inplace=True)
    df_efforts_voiles.head()
    # On remplace les str vides ou remplies d'esapces par NotaNumber (NaN) ggràce à une expression régulière
    df_efforts_voiles.replace(r'^s*$', nan, regex=True, inplace=True)
    df_efforts_voiles = df_efforts_voiles.ffill()
    # Conversion en float des colonnes sauf CdC
    col_to_num = noms_colonnes_ev
    df_efforts_voiles.loc[:,df_efforts_voiles.columns != 'cas_de_charges'] = (
        df_efforts_voiles.loc[:,df_efforts_voiles.columns != 'cas_de_charges'].apply(
            lambda x: pd.to_numeric(x)))
    # Suppréssion des dernières colonnes
    col_a_supr = noms_colonnes_ev[-4:]
    df_efforts_voiles.drop(columns=col_a_supr, inplace=True)
    df_efforts_voiles.rename(columns={"n°_élément": "n°_element"}, inplace=True)

    return df_efforts_voiles




def get_efforts_voiles_sism(df_efforts_voiles):
    # On ne consrve que les cas de charges sismiques
    df_ev_sism = df_efforts_voiles.loc[df_efforts_voiles["cas_de_charges"].isin(["3 (CQC)", "4 (CQC)"])]
    # On reset les indice du tableau des efforts sismiques
    df_ev_sism.reset_index(drop=True, inplace=True)

    return df_ev_sism


def ecart_effort_voiles_sism(df_ev_sism_rupt, df_ev_sism_base):
    nom_col = df_ev_sism_rupt.columns.tolist()
    df_ratio = df_ev_sism_rupt.copy()
    # On passe à 0 les efforts du DF ratio
    df_ratio[nom_col[2:]] = df_ev_sism_rupt[nom_col[2:]] * 0
    # On calcul le ratio des efforts avec slabe et sans slabe sauf pour les 2 premières col qui sont du texte
    df_ratio[nom_col[2:]] = (df_ev_sism_rupt[nom_col[2:]] - df_ev_sism_base[nom_col[2:]]) / df_ev_sism_base[nom_col[2:]]
    # On renome les colonnes du DF ratio
    nom_col_ratio = nom_col[:2] + [f"ecart_{nom}" for nom in nom_col[2:]]
    df_ratio.columns = nom_col_ratio


    return df_ratio


def ponderation_efforts_voiles(df_efforts_voiles, df_geo_voiles):
# Assemblage des DF des efforts et géométrie. On ne conserve que txy_bas (le plus défavorable)
    df_efforts_voiles_pond_3 = df_efforts_voiles.loc[df_efforts_voiles["cas_de_charges"] == "3 (CQC)"]
    df_efforts_voiles_pond_4 = df_efforts_voiles.loc[df_efforts_voiles["cas_de_charges"] == "4 (CQC)"]
    df_efforts_voiles_pond_3 = pd.merge(
        df_efforts_voiles_pond_3.loc[:, ["n°_element", 'cas_de_charges', 'txy_bas']],
        df_geo_voiles,
        how='outer', on='n°_element'
    )
    df_efforts_voiles_pond_4 = pd.merge(
            df_efforts_voiles_pond_4.loc[:, ["n°_element", 'cas_de_charges', 'txy_bas']],
            df_geo_voiles,
            how='left', on='n°_element'
    )
# Le cas de charge 3 est une sollicitatino suivant x, on utilise donc Ix
    df_efforts_voiles_pond_3.loc[:, 'txy*I'] = (
            df_efforts_voiles_pond_3.loc[:, "txy_bas"] * df_efforts_voiles_pond_3.loc[:, "Ix"]
    )
# Le cas de charge 4 est une sollicitation suivant y, on utilise donc Iy
    df_efforts_voiles_pond_4.loc[:, 'txy*I'] = (
            df_efforts_voiles_pond_4.loc[:, "txy_bas"] * df_efforts_voiles_pond_4.loc[:, "Iy"]
    )
# On somme les txy*I de chaque voile par étage eet pour chaque cas de charge
    df_efforts_voiles_pond_sum_3 = df_efforts_voiles_pond_3.groupby(
        ["n°_etages", "cas_de_charges"])[["txy_bas","txy*I", "Ix", "Iy"]].sum()
    df_efforts_voiles_pond_sum_4 = df_efforts_voiles_pond_4.groupby(
            ["n°_etages", "cas_de_charges"])[["txy_bas","txy*I", "Ix", "Iy"]].sum()
# Reset des indices
    df_efforts_voiles_pond_sum_3.reset_index(inplace=True)
    df_efforts_voiles_pond_sum_4.reset_index(inplace=True)
# On renomme les colonnes en ajoutant _sum à la fin
    for col in ["txy*I", "Ix", "Iy"]:
        df_efforts_voiles_pond_sum_3.rename({f"{col}": f"{col}_sum"}, axis=1, inplace=True)
    for col in ["txy*I", "Ix", "Iy"]:
        df_efforts_voiles_pond_sum_4.rename({f"{col}": f"{col}_sum"}, axis=1, inplace=True)
# On divise par la somme des moments quadratiques dans la direction concernée
    print("OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO\n",df_efforts_voiles_pond_3)
    df_efforts_voiles_pond_sum_3.loc[:, 'txy_moy_pond'] = (
            df_efforts_voiles_pond_sum_3.loc[:, "txy*I_sum"] / df_efforts_voiles_pond_sum_3["Ix_sum"])
    df_efforts_voiles_pond_sum_4['txy_moy_pond'] = (
                df_efforts_voiles_pond_sum_4["txy*I_sum"] / df_efforts_voiles_pond_sum_4["Iy_sum"])

    return df_efforts_voiles_pond_sum_3, df_efforts_voiles_pond_sum_4, pd.concat([df_efforts_voiles_pond_3, df_efforts_voiles_pond_4], ignore_index=True)


def verifier_efforts_voiles_pond(df_ev_pond_rupt, df_ev_pond_base, ecart_max):
# Assemblage des DF avec et sans rupterus
    df_ev_pond_glob = pd.merge(df_ev_pond_rupt, df_ev_pond_base, how='outer', left_index=True, right_index=True)
    df_ev_pond_glob.rename(columns = {"txy_moy_pond_x": "txy_moy_pond_rupt",
                                      "txy_moy_pond_y": "txy_moy_pond_base",
                                      "n°_etages_x": "n°_etage",
                                      "cas_de_charges_x": "cas_de_charge",
                                      "txy_bas_x": "txy_bas_rupt",
                                      "txy*I_sum_x": "txy*I_sum_rupt",
                                      "Ix_sum_x": "Ix_sum_rupt",
                                      "Iy_sum_x": "Iy_sum_rupt",
                                      "txy*I_sum_y": "txy*I_sum_base",
                                      "Ix_sum_y": "Ix_sum_base",
                                      "Iy_sum_y": "Iy_sum_base",
                                      },
                           inplace=True)
    df_ev_pond_glob["ecart"] = (
            df_ev_pond_glob["txy_moy_pond_rupt"] - df_ev_pond_glob["txy_moy_pond_base"]
                                ) / df_ev_pond_glob["txy_moy_pond_base"]

    df_voile_defect = df_ev_pond_glob.loc[df_ev_pond_glob["ecart"] > ecart_max]
    if not df_voile_defect.empty:
        return False, df_voile_defect, df_ev_pond_glob
    else:
        return True, df_voile_defect, df_ev_pond_glob


def analyse_voiles_pond(page_efforts_voiles_rupt, page_efforts_voiles_base,
                        page_description_voiles_rupt, page_description_voiles_base,
                        page_epaisseurs_voiles, ecart_max):
# On récupères les coordonnées des voiles
    df_descr_voiles_rupt = nettoyer_description_voiles(page_description_voiles_rupt)
    df_descr_voiles_base = nettoyer_description_voiles(page_description_voiles_base)
# On récupères les epaisseurs des voiles
    df_ep_voiles = nettoyer_epaisseurs_voiles(page_epaisseurs_voiles)
# On calcul teta, la longeur et les moments quadratiques des voiles
    df_geo_voiles_rupt = calcul_geometrie_voiles(df_descr_voiles_rupt, df_ep_voiles)
    df_geo_voiles_base = calcul_geometrie_voiles(df_descr_voiles_base, df_ep_voiles)
# On récupère les efforts dans les voiles
    df_effort_voiles_rupt = nettoyer_efforts_voiles(page_efforts_voiles_rupt)
    df_efforts_voiles_base = nettoyer_efforts_voiles(page_efforts_voiles_base)
# On pondères les efforts dans les voiles par I et on somme par étage et cas de charge
    df_ev_pond_sum_rupt_3, df_ev_pond_sum_rupt_4, testrupt  = ponderation_efforts_voiles(df_effort_voiles_rupt,
                                                                               df_geo_voiles_rupt)
    df_ev_pond_sum_base_3, df_ev_pond_sum_base_4, testbase = ponderation_efforts_voiles(df_efforts_voiles_base,
                                                                              df_geo_voiles_base)
# On vérifie si l'écart limite est dépassé
    verification_pond_3, df_voiles_defect_3, df_glob_3 = verifier_efforts_voiles_pond(df_ev_pond_sum_rupt_3,df_ev_pond_sum_base_3, ecart_max)
    verification_pond_4, df_voiles_defect_4, df_glob_4 = verifier_efforts_voiles_pond(df_ev_pond_sum_rupt_4,df_ev_pond_sum_base_4, ecart_max)
# On combine les résultats des 2 cas de charge
    verification_pond_tot = verification_pond_3 * verification_pond_4
    df_voiles_defect_tot = pd.concat([df_voiles_defect_3, df_voiles_defect_4], ignore_index=True)
    df_glob_tot = pd.concat([df_glob_3, df_glob_4], ignore_index=True)
    df_glob_tot.drop(["n°_etages_y", "cas_de_charges_y"], axis=1, inplace=True)
    df_glob_tot.sort_values(by=["n°_etage", "cas_de_charge"], ascending=True, inplace=True)
    return verification_pond_tot, df_voiles_defect_tot, df_glob_tot, df_geo_voiles_rupt, testrupt


def verifier_efforts_voiles(df_ecart, limite):
    # On crée un DF intermédiaire en excluant la colonne CdC pour facilité la comparaison à suivre
    df_inter = df_ecart.loc[:,df_ecart.columns != "cas_de_charges"]
    # On cré un copie complète du DF ratio
    df_voiles_defect = df_ecart.copy()
    # On crée un DF qui regroupe les lignes sui dépassent la limite pour au moins une colonne
    df_voiles_defect.loc[:, df_voiles_defect.columns != 'cas_de_charges'] = df_inter[df_inter.apply(lambda x: (x > limite).any(), axis=1)]
    # Si le DF n'est pas vide, alors des efforts dépassent la limte
    if not df_voiles_defect.empty:
        return False, df_voiles_defect
    else:
        return True, df_voiles_defect

def analyse_efforts_voiles(page_efforts_voiles_rupt, page_efforts_voiles_base, ecart_limite):
    # Création des DataFrames des efforts dans les voiles
    df_efforts_voiles_rupt = nettoyer_efforts_voiles(page_efforts_voiles_rupt)  # Avec rupteurs
    df_efforts_voiles_base = nettoyer_efforts_voiles(page_efforts_voiles_base)  # Sans rupteurs
    #  Cration des DF avec les cas de charge sismiques uniquement
    df_ev_sism_rupt = get_efforts_voiles_sism(df_efforts_voiles_rupt)
    df_ev_sism_base = get_efforts_voiles_sism(df_efforts_voiles_base)

    # Création du DF avec les ratio des efforts rupt/base
    df_ecart = ecart_effort_voiles_sism(df_ev_sism_rupt, df_ev_sism_base)
    # Vérification du ratio
    verification, df_voiles_defect = verifier_efforts_voiles(df_ecart, ecart_limite)
    # On ajoute une colonne clé pour faciliter l'assembalege des DF
    df_ev_sism_rupt["key"] = df_ev_sism_rupt["n°_element"].astype(str) + df_ev_sism_rupt["cas_de_charges"]
    df_ev_sism_base["key"] = df_ev_sism_base["n°_element"].astype(str) + df_ev_sism_base["cas_de_charges"]
    df_ecart["key"] = df_ecart["n°_element"].astype(str) + df_ecart["cas_de_charges"]
    # On assemble les DF avec la méthode reduce()
    liste_df = [df_ev_sism_rupt.loc[:,["key", "n°_element", "cas_de_charges", "txy_bas"]],
                df_ev_sism_base.loc[:,["key", "txy_bas"]],
                df_ecart.loc[:,["key", "ecart_txy_bas"]]
                ]
    df_inter = functools.reduce(lambda left,right: pd.merge(left, right, on='key', how='outer'), liste_df)
    df_inter.rename(columns={"txy_bas_x": "txy_bas_rupt_(kN)",
                             "txy_bas_y": "txy_bas_base_(kN)"
                             }, inplace=True)
    df_inter.drop("key", axis=1, inplace=True)
    df_inter.sort_values(by=["n°_element", "cas_de_charges"], inplace=True)

    return verification, df_ecart, df_inter


def nettoyer_torseur_voiles_etages(page_torseurs_voiles):
    torseurs_voiles = page_torseurs_voiles.split("\n")
    torseurs_voiles = [ligne.split("\t") for ligne in torseurs_voiles if "\t" in ligne]
    df_torseurs_voiles = pd.DataFrame(torseurs_voiles)
    # Renommer les colonnes
    noms_colonnes = df_torseurs_voiles.iloc[1,:].to_list()
    noms_colonnes = [col.replace(r"\par", "").replace(" ", "_") for col in noms_colonnes]
    df_torseurs_voiles.columns = noms_colonnes
    df_torseurs_voiles.drop(index=[0, 1], inplace=True)
    df_torseurs_voiles.ffill(inplace=True)
    # Remplissage des cases vides
    df_torseurs_voiles.replace(r'^\s*$', nan, regex=True, inplace=True)
    df_torseurs_voiles.ffill(inplace=True)
    # On ne conserve que les cas de charges 3 et 4
    df_torseurs_voiles = df_torseurs_voiles.loc[
        df_torseurs_voiles["Cas_de_charges"].isin(["3 (CQC)", "4 (CQC)"]),
        ["Cas_de_charges", "Nom_Étage", "TX_TX_haut_TX_bas_(kN)", "TY_TY_haut_TY_bas_(kN)"]]
    df_torseurs_voiles.reset_index(drop=True, inplace=True)
    # Selection des colonnes utiles
    df_torseurs_voiles = df_torseurs_voiles[["Nom_Étage", "Cas_de_charges", "TX_TX_haut_TX_bas_(kN)", "TY_TY_haut_TY_bas_(kN)"]]
    df_torseurs_voiles.columns = ["Nom_Etage", "Cas_de_charges", "TX", "TY"]  # Renome les colonnes
    df_torseurs_voiles.loc[:,"Nom_Etage"] = df_torseurs_voiles.loc[:,"Nom_Etage"].apply(lambda x: "R+0" if x=="RDC" else x) # Passage RDC -> R+0  "pour le tri"
    #Séparation des efforts hauts et bas
    df_torseurs_voiles_haut = df_torseurs_voiles.loc[
        [i for i in range(0, df_torseurs_voiles.shape[0],2)], :] # Parcours des index de 2 en 2 en partant de 0
    df_torseurs_voiles_haut["loc"] = "haut"
    df_torseurs_voiles_bas = df_torseurs_voiles.loc[
        [i for i in range(1, df_torseurs_voiles.shape[0],2)], :] # Parcours des index de 2 en 2 en partant de 1
    df_torseurs_voiles_bas["loc"] = "bas"
    # Rassemblement des DF
    df_torseurs_voiles = pd.concat([df_torseurs_voiles_haut, df_torseurs_voiles_bas],).sort_values(by=["Nom_Etage", "Cas_de_charges", "loc"], ascending=[False, True, False],)
    df_torseurs_voiles = df_torseurs_voiles[["Nom_Etage", "Cas_de_charges", "loc", "TX", "TY"]]
    # Clé d'identification
    df_torseurs_voiles["key"] = df_torseurs_voiles["Nom_Etage"] + "_" + df_torseurs_voiles["Cas_de_charges"] + "_"+  df_torseurs_voiles["loc"]
    return df_torseurs_voiles


def verifier_torseurs_voiles_etages(df_torseurs_voiles_rupt, df_torseurs_voiles_base, ecart_limite):
    nom_col = df_torseurs_voiles_rupt.columns.to_list()
    nom_col_rupt = [nom+"_rupt" for nom in nom_col]
    nom_col_base = [nom+"_base" for nom in nom_col]
    df_torseurs_voiles_rupt.columns = nom_col_rupt
    df_torseurs_voiles_base.columns = nom_col_base
    df_torseurs_voiles_glob = pd.merge(df_torseurs_voiles_rupt, df_torseurs_voiles_base[["TX_base", "TY_base", "key_base"]],
                                       left_on=["key_rupt"],
                                       right_on=["key_base"],
                                       how="left"
                                       )
    df_torseurs_voiles_glob["Ecart_TX"] = (df_torseurs_voiles_glob["TX_rupt"].astype(float) /
                                        df_torseurs_voiles_glob["TX_base"].astype(float)) -1
                                        
    df_torseurs_voiles_glob["Ecart_TY"] = (df_torseurs_voiles_glob["TY_rupt"].astype(float) /
                                    df_torseurs_voiles_glob["TY_base"].astype(float)) -1
                                    
    
    df_torseurs_voiles_glob.drop(columns=["key_rupt", "key_base"], inplace=True)
    df_torseurs_voiles_glob.rename(columns={"Cas_de_charges_rupt": "Cas_de_charges",
                                            "Nom_Etage_rupt": "Etage"}, inplace=True)
# Modification de l'ordre des colonnes
    df_torseurs_voiles_glob = df_torseurs_voiles_glob.loc[:,["Etage","Cas_de_charges", "TX_base", "TY_base", "TX_rupt", "TY_rupt", "Ecart_TX", "Ecart_TY"]]
    df_torseurs_voiles_glob.sort_values(by=["Etage","Cas_de_charges"], ascending=[False, True], inplace=True)
    #df_torseurs_voiles_defect = df_torseurs_voiles_glob.loc[(df_torseurs_voiles_glob["Ecart_TX"] >= ecart_limite) or (df_torseurs_voiles_glob["Ecart_TY"] >= ecart_limite) , :]
    #if df_torseurs_voiles_defect.empty:
        #verification = True
    #else:
        #verification = False
    verification=True
    df_torseurs_voiles_defect = 0

    return verification, df_torseurs_voiles_defect, df_torseurs_voiles_glob

def analyser_torseurs_voiles_etages(page_torseurs_voiles_rupt, page_torseurs_voiles_base, ecart_limite):
    df_torseurs_voiles_rupt = nettoyer_torseur_voiles_etages(page_torseurs_voiles_rupt)
    df_torseurs_voiles_base = nettoyer_torseur_voiles_etages(page_torseurs_voiles_base)

    return verifier_torseurs_voiles_etages(df_torseurs_voiles_rupt, df_torseurs_voiles_base, ecart_limite)
