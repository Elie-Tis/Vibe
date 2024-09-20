import pandas as pd


def to_df(liste):
    # Fonction qui permet de transformer les listes de listes en DF
    new = []
    for i in liste:
        if type(i) == list:
            i = "".join(str(elem) for elem in i)
        new.append(i.strip())
    df_new = pd.DataFrame(new)

    return df_new

def nettoyer_geometrie(page_geometrie):
    page_geo = page_geometrie.split("\n")
    page_geo = [ligne.split("\t") for ligne in page_geo]
    df_geo = pd.DataFrame(page_geo[5:8])

    return df_geo


# La géométrie varie dès que l'on ajoute les rupteurs, la comparaison sera toujours fausse même si le modèle est bon.
# On preferera donc effectuer cette vérification à la main
def verifier_geometrie(page_geo_rupteur, page_geo_base):
    verification = page_geo_rupteur == page_geo_base
    return verification, page_geo_rupteur, page_geo_base


def analyse_geometrie(page_geo_rupt, page_geo_base):

    df_geometrie_rupt = nettoyer_geometrie(page_geo_rupt)
    df_geometrie_base = nettoyer_geometrie(page_geo_base)
    df_geo_global = df_geometrie_rupt.merge(df_geometrie_base, how="outer", left_index=True, right_index=True)
    #df_geo_global.columns = ["Géométrie avec rupteurs", "Géométrie sans rupteur"]

    return df_geometrie_rupt, df_geometrie_base



def nettoyer_hypotheses(page_hypothese):
    hypotheses = []
    page_hypothese = page_hypothese.split("\n")
    page_hypothese = [ligne.split("\t") for ligne in page_hypothese]
    hypotheses = page_hypothese[8] + page_hypothese[10] + page_hypothese[12:30]
    
    return hypotheses



def verifier_hypotheses(hypo_rupt, hypo_base):
    #verification = hypo_rupt == hypo_base
    df_hypo_rupt = to_df(hypo_rupt)
    df_hypo_base = to_df(hypo_base)
    df_hypo_glob = df_hypo_rupt.merge(df_hypo_base, how='outer', left_index=True, right_index=True)
    df_hypo_glob.columns = ["Hypothèses avec rupteur", "Hypothèses sans rupteur"]
    df_hypo_glob["Identique"] = df_hypo_glob["Hypothèses avec rupteur"] == df_hypo_glob["Hypothèses sans rupteur"]
    verification = not any(df_hypo_glob.Identique == False)

    return verification, df_hypo_glob
    


def analyse_hypotheses(page_hypo_rupteur, page_hypo_base):
    hypo_rupteur = nettoyer_hypotheses(page_hypo_rupteur)
    hypo_base = nettoyer_hypotheses(page_hypo_base)
    verification, hypo_glob = verifier_hypotheses(hypo_rupteur, hypo_base)

    return verification, hypo_glob


    
    
    