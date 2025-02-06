import pandas as pd
import re


# Récupération des données valeurs modales et création du DataSet
def nettoyer_valeurs_modales(page):
    valeurs_modales = page.split('\n')
    valeurs_modales = [ligne.split("\t") for ligne in valeurs_modales if "\t" in ligne]
    df_valeurs_modales = pd.DataFrame(valeurs_modales)  # Création du DataFrame
    # On nomme les colonnes du DS, la dernière colonne est vide donc à supprimer
    nom_colonnes = ['Mode_N',
                    'Pulsation_Radps',
                    'Periode_s',
                    'Frequence_Hz',
                    'Energie_J',
                    'Mx_kgpc',
                    'My_kgpc',
                    'A_supprimer',
                    'Amortissement_pc',
                    'A_supprimer'
                    ]
    print(df_valeurs_modales)
    df_valeurs_modales.columns = nom_colonnes
    # Nettoyage du DataSet
    df_valeurs_modales = df_valeurs_modales.drop('A_supprimer', axis=1)  # Suppression définitive de la dernière colonne
    df_valeurs_modales = df_valeurs_modales.drop(index=[0, 1, 2])  # Suppression des 3 premières lignes
    # Création de la chaine de caractères recherchées en expression régulière pour extraire les valeurs
    regex = re.compile(r'\d+\.?\d*')
    # On récupère les valeurs des masses en kg et % dans Mx_kgpc et My_kgpc et on crée les colonnes correspondantes
    df_valeurs_modales[["Mx_kg", "Mx_pc"]] = tuple(df_valeurs_modales.Mx_kgpc.apply(
        lambda x: (re.findall(regex, x))))  # On crée 2 colonnes Mx et on y assigne les valeurs kg et pourcentage
    df_valeurs_modales[["My_kg", "My_pc"]] = tuple(
        df_valeurs_modales.My_kgpc.apply(lambda x: (re.findall(regex, x))))  # Idem pour My
    df_valeurs_modales = df_valeurs_modales.drop(["Mx_kgpc", "My_kgpc"],
                                                 axis=1)  # Suppression de la colonne My et My d'origine
    df_valeurs_modales_init = df_valeurs_modales.copy()  # On crée une copie du DS initial au cas où on en aurait besoin
    df_valeurs_modales = df_valeurs_modales.loc[~df_valeurs_modales['Mode_N'].isin(
        ['résiduel', ' Total '])]  # On ne conserve que les lignes qui en sont pas résiduels et Total
    df_valeurs_modales = df_valeurs_modales.apply(lambda x: pd.to_numeric(x))  # On convertit les data en float

    return df_valeurs_modales, df_valeurs_modales_init


# Récupérations des modes préponderants et des valeurs de fréquences et de masses associées, pour chaque axe
def get_valeurs_modales_prep(dataframe):
    # Création du DF relatif aux modes préponderant suivant les axes X et Y
    m_prep_x, m_prep_y = dataframe['Mx_kg'].max(), dataframe["My_kg"].max()  # On récupère les masses modales maximales
    # suivant chaque axe qu'on nomme m_prep car elles correspondent aux modes préponderants
    colonnes_interet = ['Mode_N',
                        'Periode_s',
                        'Frequence_Hz',
                        'Mx_kg',
                        'Mx_pc',
                        'My_kg',
                        'My_pc']  # Colonnes dans lesquelles ont veut récupérer les valeurs associées aux masses modales max
    # On sépare la recherche des masses suivant x et y car il est possible d'avoir le m^me mode prépondérant sur les 2 axes
    df_val_mod_prep_x = dataframe.loc[dataframe['Mx_kg'] == m_prep_x, colonnes_interet]
    df_val_mod_prep_x["Direction"] = "x"   # On ajoute une colonne pour indiquer la direction prépondérante
    df_val_mod_prep_y = dataframe.loc[ dataframe['My_kg'] == m_prep_y, colonnes_interet]
    df_val_mod_prep_y["Direction"] = "y"
    df_val_mod_prep = pd.concat([df_val_mod_prep_x, df_val_mod_prep_y], axis=0, ignore_index=True)
    df_val_mod_prep.sort_values(by='Mx_kg', ascending=False,
                                inplace=True)  # On trie le DF pour placer les valeurs relatives à l'axe X en premier


    #Récupération des valeurs modales des modes prépondérants
    mode_prep_x, mode_prep_y = df_val_mod_prep['Mode_N'].values  # On récupère les modes prépondérants
    freq_prep_x, freq_prep_y = df_val_mod_prep[
        'Frequence_Hz'].values  # On récupère les fréquences des modes préponderants
    df_val_mod_prep = df_val_mod_prep.reindex(
        ['Direction', 'Rupteurs', 'Mode_N', 'Periode_s', 'Frequence_Hz', 'Mx_kg', 'Mx_pc', 'My_kg', 'My_pc'], axis=1)


    valeurs_modales_prep = {'x': {"Mode_N": mode_prep_x,
                                  "Frequence_Hz": freq_prep_x,
                                  "Mx_kg": m_prep_x
                                  },
                            'y': {"Mode_N": mode_prep_y,
                                  "Frequence_Hz": freq_prep_y,
                                  "My_kg": m_prep_y
                                  }
                            }

    return valeurs_modales_prep, df_val_mod_prep


def verif_ecart_val_mod(val_mod_rupt_prep, val_mod_base_prep, ecart_max_pc):
    # On calcul les écarts des fréquences rupteurs et base, selon les 2 axes
    ecart_freq_x = (abs(val_mod_rupt_prep['x']['Frequence_Hz'] -val_mod_base_prep['x']['Frequence_Hz']) /
                    val_mod_base_prep['x']['Frequence_Hz'])

    ecart_freq_y = (abs(val_mod_rupt_prep['x']['Frequence_Hz'] -val_mod_base_prep['x']['Frequence_Hz']) /
                    val_mod_base_prep['x']['Frequence_Hz'])
    # Vérification sur chaque axe par rapport à l'écart max
    if ecart_freq_x >= ecart_max_pc/100 or ecart_freq_y >= ecart_max_pc/100:
        verification = False
    else:
        verification = True

    return verification, ecart_freq_x, ecart_freq_y





def analyse_valeurs_modales(page_val_mod_rupt, page_val_mod_base, ecart_max_freq_pc,):

    # Création des DataFrame des valeurs modales avec et sans rupteur
    df_val_mod_rupt, df_val_mod_rupt_init = nettoyer_valeurs_modales(page_val_mod_rupt)  # Avec rupteurs
    df_val_mod_base, df_val_mod_base_init = nettoyer_valeurs_modales(page_val_mod_base)  # Sans rupteur
    # Récupération des valeurs modales des modes prépondérants avec et sans rupteurs
    val_mod_rupt_prep, df_val_mod_rupt_prep = get_valeurs_modales_prep(df_val_mod_rupt)  # Avec rupteurs
    val_mod_base_prep, df_val_mod_base_prep = get_valeurs_modales_prep(df_val_mod_base)  # Sans rupteur
    # On rajoute une colonne dans le DF pour informer sur la présence de rupteurs
    df_val_mod_rupt_prep["Rupteurs"] = "Oui"
    df_val_mod_base_prep["Rupteurs"] = "Non"
    # On crée un DF en rassemblant les DF avec et sans rupteur
    df_val_mod_prep = pd.concat([df_val_mod_rupt_prep, df_val_mod_base_prep]).sort_values(by=['Direction', "Rupteur"],
                                                                                          ascending=[True, False])

    # Calcul des ratios de fréquences des modes prépondérants
    verif_freq, ecart_freq_x, ecart_freq_y = verif_ecart_val_mod(val_mod_rupt_prep, val_mod_base_prep, ecart_max_freq_pc)


    return verif_freq, df_val_mod_prep, ecart_freq_x, ecart_freq_y
