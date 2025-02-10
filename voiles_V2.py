from numpy import nan, sin, cos, arctan
import pandas as pd
import re
import functools


def calc_ecart(x, y):
    return (x - y) / y

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


def verif_voile_indiv(df_ev_sism_r, df_ev_sism_b):

    df_ev_sism_r.columns = [name+"_r" for name in df_ev_sism_r.columns]
    df_ev_sism_r["key"] = df_ev_sism_r["n°_element_r"].astype(str) + df_ev_sism_r["cas_de_charges_r"].astype(str)

    df_ev_sism_b.columns = [name+"_b" for name in df_ev_sism_b.columns]
    df_ev_sism_b["key"] = df_ev_sism_b["n°_element_b"].astype(str) + df_ev_sism_b["cas_de_charges_b"].astype(str)
    df_ecart_indiv = pd.merge(df_ev_sism_r, df_ev_sism_b, how="outer", on="key")
    df_ecart_indiv["ecart_txy_bas"] = df_ecart_indiv.apply(lambda row: pd.Series(calc_ecart(x=row["txy_bas_r"], y=row["txy_bas_b"])), axis=1)
    df_ecart_indiv["ecart_txy_haut"] = df_ecart_indiv.apply(lambda row: pd.Series(calc_ecart(x=row["txy_haut_r"], y=row["txy_haut_b"])), axis=1)

    return df_ecart_indiv


def analyse_voile_indiv(page_efforts_voiles_rupt, page_efforts_voiles_base, ecart_max):
    df_ev_r = nettoyer_efforts_voiles(page_efforts_voiles_rupt)
    df_ev_b = nettoyer_efforts_voiles(page_efforts_voiles_base)
    df_ev_sism_r = get_efforts_voiles_sism(df_ev_r)
    df_ev_sism_b = get_efforts_voiles_sism(df_ev_b)
    df_ecart_indiv = verif_voile_indiv(df_ev_sism_r, df_ev_sism_b)
    df_voiles_defect = df_ecart_indiv[(df_ecart_indiv["ecart_txy_bas"] > ecart_max)]
    df_voiles_defect = df_ecart_indiv[(df_ecart_indiv["ecart_txy_haut"] > ecart_max)]
    df_voiles_defect.reset_index(drop=True, inplace=True)
    verif_v_indiv = True if df_voiles_defect.empty else False
    return verif_v_indiv, df_ecart_indiv, df_voiles_defect



def nettoyer_torseur_voiles_int_etages(page_torseurs_voiles_int):
    torseurs_voiles = page_torseurs_voiles_int.split("\n")
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
        ["Cas_de_charges", "Nom_du_groupe_de_voiles", "TX_TX_haut_TX_bas_(kN)", "TY_TY_haut_TY_bas_(kN)"]]
    df_torseurs_voiles.reset_index(drop=True, inplace=True)
    df_torseurs_voiles = df_torseurs_voiles[["Nom_du_groupe_de_voiles", "Cas_de_charges", "TX_TX_haut_TX_bas_(kN)", "TY_TY_haut_TY_bas_(kN)"]]
    df_torseurs_voiles.columns = ["Nom_du_groupe_de_voiles", "Cas_de_charges", "TX", "TY"]
   

    df_torseurs_voiles_haut = df_torseurs_voiles.loc[
        [i for i in range(0, df_torseurs_voiles.shape[0],2)], :] # Parcours des index de 2 en 2 en partant de 0
    df_torseurs_voiles_haut["loc"] = "haut"
    # On cherche le nombre d'étage dans le bât
    etage_max = int(df_torseurs_voiles_haut.loc[df_torseurs_voiles_haut["Cas_de_charges"] == "3 (CQC)"].shape[0])
    etages = [f"R+{etage}" for etage in range(etage_max)]  # Liste des étages en mode R+i
    #On ajoute le colonne etage
    for cdc in df_torseurs_voiles_haut["Cas_de_charges"].unique():
            filtre = (df_torseurs_voiles_haut["Cas_de_charges"] == cdc)
            df_torseurs_voiles_haut.loc[filtre, "Etage"] = etages

    df_torseurs_voiles_bas = df_torseurs_voiles.loc[
        [i for i in range(1, df_torseurs_voiles.shape[0],2)], :] # Parcours des index de 2 en 2 en partant de 1
    df_torseurs_voiles_bas["loc"] = "bas"
    # On ajoute la colonne étage
    for cdc in df_torseurs_voiles_bas["Cas_de_charges"].unique():
            filtre = (df_torseurs_voiles_bas["Cas_de_charges"] == cdc)
            df_torseurs_voiles_bas.loc[filtre, "Etage"] = etages


    df_torseurs_voiles = pd.concat([df_torseurs_voiles_haut, df_torseurs_voiles_bas],).sort_values(by=["Etage", "Cas_de_charges", "loc"], ascending=[False, True, False],)
    df_torseurs_voiles = df_torseurs_voiles[["Etage", "Cas_de_charges", "loc", "TX", "TY"]]
    df_torseurs_voiles["key"] = df_torseurs_voiles["Etage"] + "_" + df_torseurs_voiles["Cas_de_charges"] + "_"+  df_torseurs_voiles["loc"]

    return df_torseurs_voiles


def verifier_torseurs_voiles_int_etages(df_torseurs_voiles_int_rupt, df_torseurs_voiles_int_base, ecart_limite):
    nom_col = df_torseurs_voiles_int_rupt.columns.to_list()
    nom_col_rupt = [nom+"_rupt" for nom in nom_col]
    nom_col_base = [nom+"_base" for nom in nom_col]
    df_torseurs_voiles_int_rupt.columns = nom_col_rupt
    df_torseurs_voiles_int_base.columns = nom_col_base
    df_torseurs_voiles_glob = pd.merge(df_torseurs_voiles_int_rupt, df_torseurs_voiles_int_base[["TX_bas_base", "key_base"]],
                                       left_on=["key_rupt"],
                                       right_on=["key_base"],
                                       how="left"
                                       )
    df_torseurs_voiles_glob["Ecart_TX"] = (df_torseurs_voiles_glob["TX_rupt"].astype(float) /
                                        df_torseurs_voiles_glob["TX_base"].astype(float) -1
                                        )
     df_torseurs_voiles_glob["Ecart_TY"] = (df_torseurs_voiles_glob["TY_rupt"].astype(float) /
                                        df_torseurs_voiles_glob["TY_base"].astype(float) -1
                                        )

    
    df_torseurs_voiles_glob.drop(columns=["key_rupt", "key_base"], inplace=True)
    df_torseurs_voiles_glob.rename(columns={"Cas_de_charges_rupt": "Cas_de_charges",
                                            "Nom_Étage_rupt": "Etage"}, inplace=True)
# Modification de l'ordre des colonnes
    df_torseurs_voiles_glob = df_torseurs_voiles_glob[["Etage","Cas_de_charges", "TX_base", "TY_base", "TX_rupt", "TYrupte", "Ecart_TX", "Ecart_TY"]]
    df_torseurs_voiles_glob.sort_values(by=["Etage","Cas_de_charges"], ascending=True, inplace=True)
    # Détection des étages défectueux
    filtre_defect = (df_torseurs_voiles_glob["Ecart_TX"] >= ecart_limite) | (df_torseurs_voiles_glob["Ecart_TY"] >= ecart_limite)
    df_torseurs_voiles_defect = df_torseurs_voiles_glob.loc[filtre_defect, :]
    if df_torseurs_voiles_defect.empty:
        verification = True
    else:
        verification = False

    return verification, df_torseurs_voiles_defect, df_torseurs_voiles_glob


def analyser_torseurs_voiles_int_etages(page_torseurs_voiles_rupt, page_torseurs_voiles_base, ecart_limite):
    df_torseurs_voiles_int_rupt = nettoyer_torseur_voiles_int_etages(page_torseurs_voiles_int_rupt)
    df_torseurs_voiles_int_base = nettoyer_torseur_voiles_int_etages(page_torseurs_voiles_int_base)

    return verifier_torseurs_voiles_int_etages(df_torseurs_voiles_int_rupt, df_torseurs_voiles_int_base, ecart_limite)

