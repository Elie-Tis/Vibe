# Lorsque les voiles ne sont pas numérotés de la même manière entre le modèle avec et sans rupteurs, la comparaison des efforts dans les voiles de manière individuelle ne peux plus se baser sur les numéros d'éléments.
# Il faut donc se rabattre sur l"utilisation des coordonées des voiles. Important de noter que cette méthode ne fonctionne pas dans le cas de modèles avec des refends désolidarisés de la façade !!!!

from numpy import nan, sin, cos, arctan
import pandas as pd
import re
import functools

# On cherche à rassembler tous les informations sur les voiles : n°, coord, epaisseur, longueur, inertie, etc

#--------------------------------------------------------------------------------------------------------------------------------------------
def nettoyer_coord_voiles(page_coord_voiles):
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
    df_description_voiles["N°_element"] = pd.to_numeric(df_description_voiles["N°_element"])
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
                                                      [f"coord_p0_{i}", f"coord_p1_{i}", f"coord_p2_{i}", f"coord_p3_{i}"]
                                                      ].max(axis=1)
        df_description_voiles.drop([f"coord_p0_{i}",f"coord_p1_{i}",f"coord_p2_{i}", f"coord_p3_{i}"], axis=1, inplace=True)
# Création d'une collonne identifiant
        df_description_voiles["id"] = [df_description_voiles["col"] for col in ["coord_x1", "coord_x2", "coord_y1", "coord_y2", "coord_z1", "coord_z2"]]
    return df_description_voiles

#------------------------------------------------------------------------------------------------------------------------------------------------------
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
  
#------------------------------------------------------------------------------------------------------------------------------------------------------
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

#----------------------------------------------------------------------------------------------------------------------------------------
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
    df_efforts_voiles.loc[:,df_efforts_voiles.columns != 'Cas_de_charges'] = (
        df_efforts_voiles.loc[:,df_efforts_voiles.columns != 'Cas_de_charges'].apply(
            lambda x: pd.to_numeric(x)))
    # Suppréssion des dernières colonnes
    col_a_supr = noms_colonnes_ev[-4:]
    df_efforts_voiles.drop(columns=col_a_supr, inplace=True)
    df_efforts_voiles.rename(columns={"N°_Élément": "N°_element"}, inplace=True)  # On évite le é majuscule
    return df_efforts_voiles

#----------------------------------------------------------------------------------------------------------------------------------------
# On filtre les cas de charges intéressants et on regroupe efforts et coordonnées
def get_efforts_voiles(df_efforts_voiles, df_coord_voiles, list_cdc=["3 (CQC)", "4 (CQC)"] ):
    df_efforts_voiles = pd.merge(df_efforts_voiles, df_coord_voiles, on="N°element")  # On assemble les efforts et des coord en fonction du numéro élément
    return df_efforts_voiles.loc[df_efforts_voiles["Cas_de_charges"].isin(list_cdc), :]   # On filtre les cas de charges recherchées
    
#----------------------------------------------------------------------------------------------------------------------------------------
def get_geo_voiles(page_coord_voiles, page_epaisseurs_voiles):
  df_coord_voiles = nettoyer_coord_voiles(page_coord_voiles)
  df_ep_voiles = nettoyer_epaisseur_voiles(page_epaisseurs_voiles)
  df_geo_voiles = calcul_geometrie_voiles(df_coord_voiles, df_ep_voiles)
  return df_geo_voiles   # Retourne un df avec les coord, et les paramètres géo, inertie, etc...
    
#----------------------------------------------------------------------------------------------------------------------------------------
# On cherche à calculer les efforts dans les voiles
def calc_ecart_effort_voiles(df_efforts_voiles_rupt, df_efforts_voiles_base, list_effort=["Txy_bas", "Txy_haut"] ):
    df_ecart_efforts_voiles = pd.merge(df_efforts_voiles_rupt, df_efforts_voiles_base, on="id", suffixes=("rupt", "base"))
    for effort in list_effort:
        df_ecart_efforts_voiles[f"ecart_abs_{effort}"] = df_ecart_efforts_voiles[f"{effort}_rupt"] - df_ecart_efforts_voiles[f"{effort}_base"]    # Ecart absolu (kN)
        df_ecart_efforts_voiles[f"ecart_rel_{effort}"] = df_ecart_efforts_voiles[f"{effort}_rupt"] / df_ecart_efforts_voiles[f"{effort}_base"] - 1  # Ecart relatif (%)
    return df_ecart_efforts_voiles


def cal_moy_pond_ecart_voiles(df_ecart_efforts_voiles, dict_cdc_dir):
    #dict_cdc_dir est un dictionnaire qui indique la direction prédominante de chaque cas de charge choisi  {"3 (CQC)": "x",  "Fx + 0.3Fy": "x", "Fy + 0.3Fx": "y"
    for (cdc,dir) in dict_cdc_dir:
        I_dir = f"I{dir}"
        filtre_cdc = df_ecart_efforts_voiles["Cas_de_charges"] == cdc
        sum_I = df_ecart_efforts_voiles.loc[filtre_cdc, f"I{dir}" ].sum()  # Calcul de la somme des inerties dans la direction de la charge
        for col_ecart in [col in df_ecart_efforts_voiles.columns if "ecart" in col]  # Pondération de chaque colonne écart
            df_ecart_efforts_voiles.loc[filtre_cdc, [f"{col_ecart}_pond"]] = df_ecart_efforts_voiles.loc[filtre_cdc, :].apply(lambda x: x.col_ecart * x.Idir / sum_I)
        df_ecart_moy_pond = df_ecart_efforts_voiles.goupby( by="Cas_de_charges", as_index=False)[col for col in df_ecart_efforts_voiles.columns if "pond" in col].mean()
    return df_ecart_moy_pond
    
         
    
    
    
