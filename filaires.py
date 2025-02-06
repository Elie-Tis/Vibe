import pandas as pd
from numpy import nan
import copy






def nettoyer_efforts_filaires(page_efforts_fil):
# Récupération des datas de la page des efforts
    efforts_fil = page_efforts_fil.split('\n')
    efforts_fil = [ligne.split("\t") for ligne in efforts_fil if ("\t") in ligne]
# Création du DataFrame
    df_efforts_fil = pd.DataFrame(efforts_fil)
# On nettoie le DF des efforts
    noms_colonnes_efforts = ["Element_N", "Cas_de_charge", "Maille", "Noeud_N","Fx", "Fy", "Fz", "Mx", "My", "Mz"]
    df_efforts_fil.columns = noms_colonnes_efforts  # On renomme les colonnes

    df_efforts_fil.drop(index=  [0], inplace= True)  # Suppression de la première ligne
# On vide completement les cellules avec des chaines de caractères vides
    df_efforts_fil.replace(r'^\s*$', nan, regex=True, inplace= True)  # On utilise l'expression régulière pour les chaines de caractères vides ou remplies uniquement d'espaces
#  On propage les valeurs des cellules dans les cellules vide d'en dessous avec la méthode ffill()
    df_efforts_fil.ffill(inplace= True)
#  On convertie les valeurs d'efforts et de moment en valeurs numériques
    for col in ["Fx", "Fy", "Fz", "Mx", "My", "Mz"]:
        df_efforts_fil[col] = pd.to_numeric(df_efforts_fil[col], errors='raise')
    df_efforts_fil["Element_N"] = df_efforts_fil["Element_N"].astype(float)
    return df_efforts_fil


def nettoyer_description_filaires(page_description_fil):
# Récupération des datas de la page de description
    description_fil = page_description_fil.split('\n')
    description_fil = [ligne.split("\t") for ligne in description_fil if ("\t") in ligne]
# Création d'un DF
    df_description_fil = pd.DataFrame(description_fil)
# On nettoie le DF
    noms_colonnes_description = ["Element_N", "Rupteur", "A_supprimer"]  # La dernière colonne du DataSet est vide
    df_description_fil.columns = noms_colonnes_description
    df_description_fil.drop('A_supprimer', axis=1, inplace=True)  # Suppression de la dernière colonne
    df_description_fil.drop(index=[0,1], inplace=True)  # Suppression des 2 premières lignes
    df_description_fil["Element_N"] = df_description_fil["Element_N"].astype(float)
    df_description_fil["Rupteur"] = df_description_fil["Rupteur"].apply(lambda x: x.strip())  # Suppression des espaces en baord de chaine de caractère

    return df_description_fil


def combiner_df_fillaires(df_efforts_fil, df_description_fil):
# On combine les deux DF en fonction de la clé "Element_N", pour retrouver le type de slabe à chaque ligne
    print(df_efforts_fil, df_description_fil)
    df_fillaires = pd.merge(df_efforts_fil, df_description_fil, how='left', on="Element_N")

    return df_fillaires


def get_effort_max_slabe(df_fillaires):
    slabe_used = pd.unique(df_fillaires["Rupteur"])  # On récupère la liste des types de rupteurs présents dans # l'étude
    print(df_fillaires["Rupteur"])
    efforts_max = {}  # Initialisation du dictionnaire qui ve contenir les efforts maximaux appliqués à chaque type de rupteur
# On cherche les efforts maximaux appliqués sur chaque type de rupteur
    for slabe in slabe_used:  # On itère sur chaque type de rupteur utilisé
# On cherche l'effort max suivant y
        fy_max = df_fillaires.loc[df_fillaires["Rupteur"] == slabe, "Fy"].max()
        fy_min = df_fillaires.loc[df_fillaires["Rupteur"] == slabe, "Fy"].min()
        if abs(fy_max) - abs(fy_min) <= 0:  # On cherche la plus grande valeur absolue
            fy_max = fy_min
#Idem suivant x
        fx_max = df_fillaires.loc[df_fillaires["Rupteur"] == slabe, "Fx"].max()
        fx_min = df_fillaires.loc[df_fillaires["Rupteur"] == slabe, "Fx"].min()
        if abs(fx_max) - abs(fx_min) <= 0:  # On cherche la plus grande valeur absolue
            fx_max = fx_min
#Idem suivant z
        fz_max = df_fillaires.loc[df_fillaires["Rupteur"] == slabe, "Fz"].max()
        fz_min = df_fillaires.loc[df_fillaires["Rupteur"] == slabe, "Fz"].min()
        if abs(fx_max) - abs(fx_min) <= 0:  # On cherche la plus grande valeur absolue
            fz_max = fz_min
# On ajoute les efforts trouvé au dictionnaire des efforts du rupteur c
        efforts_max[slabe] = {"Fy": fy_max, "Fx": fx_max, "Fz": fz_max}

    return efforts_max


def verifier_efforts_slabe(efforts_max, resistance_slabe, gamma):
# On initialise le bool validation à True
    validation = True
#Création d'un dictionnaire qui va contenir des bool pour chaque effort de chaque type de rupteur
    resistance_slabe_verifiee = copy.deepcopy(efforts_max)  # d1 = d2 ne crée pas une copie indépendante, il faut utiliser la méthode deepcopy
    for slabe in efforts_max:  # On itère sur tous les typs de rupteurs utilisés
        print("EFFORT MAX :: ","\n",efforts_max)
        for effort in efforts_max[slabe]:  # On itère sur tous les efforts
# On vérifie si l'effort ne dépasse pas l'effort resistant du rupteur
            res_slabe = 0 if not slabe in resistance_slabe else resistance_slabe.get(slabe).get(effort+"_Rd")  # On evite l'erreur de clée inexistante dans le dict (mauvais matériaux)
            resistance_verifiee = abs(efforts_max[slabe][effort]) * gamma - res_slabe <= 0
            if resistance_verifiee == False or res_slabe==0:  # On passe validation a 0 si un des efforts resistant est dépassé ou si erreur matériaux
                validation = False
            resistance_slabe_verifiee[slabe][effort] = resistance_verifiee


    return resistance_slabe_verifiee, validation


def lister_rupteur_defect(df_fil, resistance_slabe, page_description_fil):
# On crée un DF avec les résistances maximales des rupteurs
    df_res_rupt = pd.DataFrame(resistance_slabe)
    df_res_rupt = df_res_rupt.transpose()
    df_res_rupt= df_res_rupt.reset_index() #On transpose et réinitialise les indexs
    df_res_rupt.rename(columns={"index": "Rupteur"}, inplace=True) # On renomme l'ancienne colonne index qui représente les types de rupteurs
# Assemblage des DF effort appliqués et résistants, avec la clée Rupteur
    df_rupt_defect = pd.merge(df_fil, df_res_rupt, how= 'left', on= 'Rupteur')
# On isole les rupteurs dont au moins un des efforts appliqué dépasse l'effort résistant
    df_rupt_defect = df_rupt_defect.loc[(abs(df_rupt_defect.Fx) > df_rupt_defect.Fx_Rd) |
                                        (abs(df_rupt_defect.Fy) > df_rupt_defect.Fy_Rd) |
                                        (abs(df_rupt_defect.Fz) > df_rupt_defect.Fz_Rd)]
# On récupère les numéros des éléments trop sollicités
    rupteur_defect_N = df_rupt_defect["Element_N"].unique()
# On récupère le DF de description des filaires pour afficher le type de rupteur defectueu
    df_defect_description = nettoyer_description_filaires(page_description_fil)
    df_defect_description = df_defect_description[df_defect_description.Element_N.isin(rupteur_defect_N)]
    df_defect_description.set_index("Element_N", inplace= True)

    return rupteur_defect_N, df_defect_description

def analyse_efforts_rupteurs(page_efforts_fil, page_description_fil, resistance_slabe, gamma):

# Creation des DF et netoyage des effort et des rupteurs utilises
    df_efforts_fil = nettoyer_efforts_filaires(page_efforts_fil)
    df_description_fil = nettoyer_description_filaires(page_description_fil)
# Combinaison des 2 DF
    df_fil = combiner_df_fillaires(df_efforts_fil, df_description_fil)
# Recuperation des efforts max appliques à chaque type de rupteur
    efforts_max = get_effort_max_slabe(df_fil)
# On verifie que les efforts appliques soient inferieurs aux efforts resistants
    resistance_slabe_verifiee, validation = verifier_efforts_slabe(efforts_max, resistance_slabe, gamma)
    if validation :

        rupteur_defect_N = False
        df_defect_description = False
    else :
# Si les efforts sont dépassés, on donne les numéros et types des rupteurs defectueux
        rupteur_defect_N, df_defect_description = lister_rupteur_defect(df_fil, resistance_slabe, page_description_fil)


    return validation, efforts_max, rupteur_defect_N, df_defect_description







            









