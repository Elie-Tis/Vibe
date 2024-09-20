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



