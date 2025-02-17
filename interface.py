import filaires
import ndc
import valeurs_modales
import voiles
import streamlit as st
import pandas as pd
import geo_hypo
import voiles_V2, voiles_V3
import plotly.express as px

########################################################################################################################
#                                         Page et la barre latéralle
########################################################################################################################

st.set_page_config(layout="wide", initial_sidebar_state ="expanded")
# Titre de la page
st.title("Analyse des notes de calculs sismiques")

#-----------------------------------------------------------------------------------------------------------------------
#                               Construction de la barre latéralle
#-----------------------------------------------------------------------------------------------------------------------
with st.sidebar:
    st.title("Notes de calcul Advancessss7777")
    with st.expander("Dépots des notes de calcul"):
# Récupération des fichiers drop dans la barre latérale
        ndc_rupteur = st.file_uploader('Avec rupteurs', type='txt')
        ndc_base = st.file_uploader('Sans rupteur', type='txt')
    st.divider()

    st.title("Paramètres de vérifications")
# Initialisation des valeurs de gamma pour DCM et DCL
    gamma_DCM=1.1
    gamma_DCL=1.0
# Choix des modification pour les valeurs de gamme
    choix_gamma = st.toggle("Modifier les valeurs de γ")
    if choix_gamma:
        gamma_DCM = st.number_input("γ_DCM",label_visibility="visible",
                                    min_value=0.0,
                                    step=0.01,
                                    value=gamma_DCM,
                                    help='Renseigner la valeur de γ = γ1 + γ2',
                                )
        gamma_DCL = st.number_input("γ_DCL",label_visibility="visible",
                                    min_value=0.0,
                                    step=0.01,
                                    value=gamma_DCL,
                                    help='Renseigner la valeur de γ = γ1 + γ2'
                                    )
# Affichage des données actuelles pour gamma
    st.info(f"γ_DCM = {round(gamma_DCM, 3)}\n\n"
            f"γ_DCL = {round(gamma_DCL, 3)}\n")
# Initialisation des écarts max pôur les différentes vérifications
    ecart_max_freq = 0.15
    ecart_max_voiles = 0.10
# Choix des modifications des écarts
    choix_ecarts = st.toggle("Modifier les écarts limites")
    if choix_ecarts:
        ecart_max_freq = st.number_input("Ecart maximal des fréquences",
                                    label_visibility="visible",
                                    min_value=0.0,
                                    step=0.01,
                                    value=ecart_max_freq,
                                )
        ecart_max_voiles = st.number_input("Ecart maximal des efforts dans les voiles",
                                           label_visibility="visible",
                                           min_value=0.0,
                                           step=0.01,
                                           value=ecart_max_voiles
                                )
# Affichage des données acuelles pour les écarts
    st.info(f"Ecart max des fréquences = {ecart_max_freq*100}%\n\n"
            f"Ecart max des efforts dans les voiles = {ecart_max_voiles*100}%")

########################################################################################################################
#                                   Construction de la page princiaple
########################################################################################################################

#-----------------------------------------------------------------------------------------------------------------------
#                               Traitement des fichiers glissés dans la barre latéralle
#-----------------------------------------------------------------------------------------------------------------------
# Passage des éléments fichiers en éléments text
if ndc_rupteur and ndc_base :
    ndc_rupteur = ndc_rupteur.getvalue().decode("utf-16") 
    ndc_base = ndc_base.getvalue().decode("utf-16")
else:
    ndc_ex = open("BAT_A_SLABE_ndc08.txt", "r", encoding="utf-16")
    ndc_rupteur = ndc_ex.read()
    ndc_ex.close()
    ndc_ex = open("BAT_A_BETON_ndc15.txt", "r", encoding="utf-16")
    ndc_base = ndc_ex.read()
    ndc_ex.close()
# Découpage des ndc en différentes pages
pages_rupteur = ndc.get_pages_st(ndc_rupteur, rupteur=True)
pages_base = ndc.get_pages_st(ndc_base, rupteur=False)

#-----------------------------------------------------------------------------------------------------------------------
#                                            Analyse de la géométrie
#-----------------------------------------------------------------------------------------------------------------------
# Récupération des DF et des indicateurs de verification pour la géométrie
df_geo_rupt, df_geo_base = geo_hypo.analyse_geometrie(pages_rupteur["Geometrie"], pages_base["Geometrie"])
# Sous titre eet séparation en 2 colonnes
st.subheader("Analyse de la géométrie")
col1, col2 = st.columns(2)
with col1:
    st.write("Géométrie du modèle avec rupteurs")
    st.dataframe(df_geo_rupt, hide_index=True)
with col2:
    st.write("Géométrie du modèle sans rupteur")
    st.dataframe(df_geo_base, hide_index=True)
st.divider()
#-----------------------------------------------------------------------------------------------------------------------
#                                            Analyse des hypothèses
#-----------------------------------------------------------------------------------------------------------------------
#Récupération des DF et indicateurs de vérification pour les hypothèses
verif_hypo, hypo_glob = geo_hypo.analyse_hypotheses(pages_rupteur["Hypotheses"], pages_base["Hypotheses"])
#Fonction qui permet de surligner les lignes du DF hypothèses qui ne sont pas identiques
def color_dif(df):
    if df.Identique:
        return ['background-color:'] * len(df)
    else:
        return ['background-color: #3e2327'] * len(df)


# Sous-titre
st.subheader("Analyse des hypothèses")
# Affichage de l'état des hypothèses
if verif_hypo:
    st.success("Les hypothèses sont les mêmes pour les 2 notes de calcul")
else:
    st.error("Attention, des différences ont été detectées dans les hypothèses !")
# Affichage du DF avec mise en valeur des différences
st.dataframe(hypo_glob.style.apply(color_dif, axis=1),  use_container_width=True, hide_index=True)
# Séparation en 2 colonnes et menu déroulant pour choisir la classe de ductilité
col_duct, _ = st.columns([1, 2])
with col_duct:
    classe_duct = st.selectbox("Selectionner la classe de ductilité", ["DCM", "DCL"], placeholder="Classe de ductilité")
# Mise à our de gamma en fonction de la classe de ductilité choisie
    gamma = gamma_DCM if classe_duct == "DCM" else gamma_DCL

#-----------------------------------------------------------------------------------------------------------------------
#                                     Analyse des modes prépondérants
#-----------------------------------------------------------------------------------------------------------------------
# Récupération des DF et des indicateurs de vérification
verif_freq, df_vm_prep, delta_f_x, delat_f_y = (valeurs_modales.analyse_valeurs_modales(
                                            pages_rupteur["Valeurs_modales"],
                                            pages_base["Valeurs_modales"],
                                            ecart_max_freq_pc=ecart_max_freq*100)
                                                )
# Sous-titre
st.subheader("Analyse des modes préponderants")
# Affichage de l'état de la vérification des écarts de fréquences
if verif_freq:
    st.success(f"Les écarts de fréquences des modes prépondérants ne dépassent pas la limite fixée de {ecart_max_freq*100} %")
else:
    st.error(f"Attention, les écarts de fréquences sont supérieurs à la limite fixée de {ecart_max_freq*100} %")
# Affichage du DF
st.dataframe(df_vm_prep, use_container_width=True, hide_index=True)
# Séparation en 2 colonnes et affichages des écarts de fréquences suivant les 2 axes
col3, col4 = st.columns(2)
with col3:
    st.info(f"Ecart des fréquences suivant x : {round(delta_f_x*100, 2)}% ")
with col4:
    st.info(f"Ecart des fréquences suivant y : {round(delat_f_y*100, 2)}%")
st.divider()
#-----------------------------------------------------------------------------------------------------------------------
#                                     Analyse des efforts dans les rupteurs
#-----------------------------------------------------------------------------------------------------------------------
# Récupération des DF et des indicateurs de vérification
resistance_slb = ndc.resistance_slabe.copy()
verif_rupt, efforts_max,_, df_rupt_defect = (filaires.analyse_efforts_rupteurs(
    pages_rupteur["Efforts_filaires"],
    pages_rupteur["Description_filaires"],
    resistance_slabe=ndc.resistance_slabe,
    gamma=gamma
    ))
# On renomme les index de efforts max
for slabe in efforts_max:
    efforts_max[slabe]["Fx_Ed"] = efforts_max[slabe].pop("Fx")
    efforts_max[slabe]["Fy_Ed"] = efforts_max[slabe].pop("Fy")
    efforts_max[slabe]["Fz_Ed"] = efforts_max[slabe].pop("Fz")
# Sous-titre
st.subheader("Analyse des efforts dans les rupteurs ")
# Affichage de l'éat des vérification des efforts dans les rupteurs
if verif_rupt:
    st.success("Les efforts appliquées aux différents rupteurs sont tous inférieurs aux efforts résistants")
else:
    st.error("Attention, certains rupteurs subissent des efforts trop importants !")
# Séparation en 4 colonnes
col5, col6, col7, col_rupt_defect = st.columns([1.9, 2.1, 2, 1.4], gap="small")
#Affichage des efforts max appliqués à chaque modèle de rupteur
with col5:
    st.write("Efforts maximaux appliqués aux rupteurs (kN)")
    df_efforts_max = pd.DataFrame(efforts_max).transpose()
    st.dataframe(abs(df_efforts_max), use_container_width=True)
# Affichage des efforts max majorés par gamme appliqués à chaque modèle de rupteur
with col6:
    st.write("Efforts max majorés appliqués aux rupteurs (kN)")
    df_efforts_max = pd.DataFrame(efforts_max).transpose()*gamma
    df_efforts_max.columns = ["Fx_Ed_maj", "Fy_Ed_maj", "Fz_Ed_maj"]
    st.dataframe(abs(df_efforts_max), use_container_width=True)
    info_gama = st.info(
        f"La classe de ductilité {classe_duct} implique d'utiliser un coefficient majorateur γ = {gamma} "
        f"lors de la vérification des efforts dans les rupteurs")
# Affichage des résistances de tous les modèles de rupteur
with col7:
    st.write("Efforts résistants des rupteurs (kN)")
    df_resistance_slb = pd.DataFrame(resistance_slb).transpose()
    st.dataframe(df_resistance_slb, use_container_width=True)
# Menu déroulant pour afficher les rupteurs trop sollicités

with col_rupt_defect:
    expander = st.expander("Voir les rupteurs trop sollicités")
    if not verif_rupt:
        with expander:
            st.dataframe(df_rupt_defect, use_container_width=True)
    else:
        st.caption("")
st.divider()
#-----------------------------------------------------------------------------------------------------------------------
#                                     Analyse des efforts dans les voiles
#-----------------------------------------------------------------------------------------------------------------------
# Récupération des DF et des indicateurs de vérification des coordonnées
verif_coord_voiles, _, _, df_verif_coord = (
    voiles.analyse_coord_voiles(
        page_coord_voiles_rupt=pages_rupteur["Coordonnées_voiles"],
        page_coord_voiles_base=pages_base["Coordonnées_voiles"]
    )
)
# Récupération des DF et des indicateurs de vérification des efforts voiles par voiles
verif_voiles_indiv, df_ecarts_efforts_voiles, df_voiles_defect = (
    voiles_V2.analyse_voile_indiv(
        page_efforts_voiles_rupt=pages_rupteur["Torseurs_voiles"],
        page_efforts_voiles_base=pages_base["Torseurs_voiles"],
        ecart_max=ecart_max_voiles
    ))


# Récupération des DF et indicateurs de vérification des torseurs (TX, TY, etc.) par étages
verif_voile_int_etage, df_voiles_int_defect_etages, df_voiles_int_glob_etages = voiles_V2.analyser_torseurs_voiles_int_etages(
    page_torseurs_voiles_int_rupt=pages_rupteur["Torseurs_etages_voiles"],
    page_torseurs_voiles_int_base=pages_base["Torseurs_etages_voiles"],
    ecart_limite=ecart_max_voiles
)
# Sous titre

def color_voil(val, limite):
    color ='#3e2327' if float(val)>limite else '#173928'
    return f'background-color: {color}'

#Vérification des efforts
st.subheader("Vérification des efforts dans les voiles")
# Vérificationd es coordonnées
# Affichage de l'état de la vérification des coordonnées des voiles
if verif_coord_voiles:
    st.success("Les coordonnées des voiles intérieurs sont indentiques dans les 2 notes de calcul")
else:
    st.warning("Attention : les coordonnées des voiles ne sont pas indentiques dans les 2 notes de calculs. "
               "Vérifier manuellement la cohérences des coordonées")
# Affichage retractable des voiles dont les coordonnées ne correspondent pas
expander2 = st.expander("Voir les voiles avec des incohérences de coordonnées")
with expander2:
    st.dataframe(df_verif_coord, hide_index=True, use_container_width=True)
#.......................................................................
# Méthode de vérification des efforts dans les voiles individuellement
#.......................................................................
with st.expander("#### *A. Vérification des voiles individuellement*"):
    if verif_voiles_indiv:
        st.success(f"Les écarts d'efforts dans les voiles intérieurs ne dépassent pas la limite fixée "
                f"de {ecart_max_voiles * 100}%")
    else:
        st.warning(f"Attention : Les écarts d'efforts dans les voiles intérieurs dépassent la limite fixée "
                f"({ecart_max_voiles * 100}%)")
    col_print = ["n°_element_r", "cas_de_charges_r", "txy_haut_r", "txy_haut_b", "ecart_txy_haut", "txy_bas_r", "txy_bas_b",
                "ecart_txy_bas"]
    # Affichage de l'état de la vérification des coordonnées
    st.dataframe(df_voiles_defect.loc[:, col_print].style.format(precision=3).map(
    func=(lambda x: color_voil(val=x, limite=ecart_max_voiles)), subset=["ecart_txy_haut", "ecart_txy_bas"]),
                    use_container_width=True)

    choix_ecarts = st.toggle("Voir la liste complète des voiles")
    if choix_ecarts:
        st.dataframe(df_ecarts_efforts_voiles.loc[:, col_print].style.format(precision=3).map(
                func=(lambda x: color_voil(val=x, limite=ecart_max_voiles)), subset=["ecart_txy_haut", "ecart_txy_bas"]),
                            use_container_width=True)
#............................................................................
# Méthode de vérification des efforts dans les voiles pondérés par l'inertie
#............................................................................
# Affichage retractable pour les résultats de la méthode
# st.markdown("#### *B. Vérification des voiles par étage avec pondération inertielle*")
# # Affichage de l'état de vérification des écarts d'effrots
# if verif_voiles_pond:
#     st.success(f"Les écarts d'efforts dans les voiles intérieurs ne dépassent pas la limite fixée "
#                f"de {ecart_max_voiles*100}%")
# else:
#     st.warning("Attention : Les écarts d'efforts dans les voiles intérieurs dépassent la limite fixée "
#                f"({ecart_max_voiles*100}%)")

# st.dataframe(df_glob_pond.loc[:,['n°_etage', "cas_de_charge", "txy_moy_pond_rupt", "txy_moy_pond_base", "ecart"]
#              ].style.format(precision=3).map(lambda x: color_voil(val=x, limite=ecart_max_voiles),subset="ecart"),
#              hide_index=True,
#              use_container_width=True)


#............................................................................
# Méthode de vérification des efforts dans les voiles avec torseurs par étages
#............................................................................
# Affichage retractable pour les résultats de la méthode
with st.expander("#### *C. Vérification des torseurs par étage*"):
# Affichage de l'état de vérification des écarts d'efforts
    if verif_voile_int_etage:
        st.success(f"Les écarts d'efforts dans les voiles intérieurs ne dépassent pas la limite fixée "
                f"de {ecart_max_voiles*100}%")
    else:
        st.warning("Attention : Les écarts d'efforts dans les voiles intérieurs dépassent la limite fixée "
                f"({ecart_max_voiles*100}%)")

    st.dataframe(df_voiles_int_glob_etages.style.format(precision=3).map(lambda x: color_voil(val=x, limite=ecart_max_voiles),subset=["Ecart_TX", "Ecart_TY"]),
                hide_index=True,
                use_container_width=True)

st.divider()


#-------------------------------------------------------------------------------
# TEST #
#---------------------------------------------------------------------------------
st.markdown("#### *TEST*")


df_efforts_voiles_rupt = voiles_V3.get_efforts_voiles(page_coord_voiles=pages_rupteur['Coordonnées_voiles'], 
                    page_epaisseurs_voiles=pages_rupteur['Epaisseurs_voiles'], 
                    page_efforts_voiles=pages_rupteur["Torseurs_voiles"],
                    list_cdc=["3 (CQC)", "4 (CQC)"])

df_efforts_voiles_base = voiles_V3.get_efforts_voiles(page_coord_voiles=pages_base['Coordonnées_voiles'], 
                    page_epaisseurs_voiles=pages_base['Epaisseurs_voiles'], 
                    page_efforts_voiles=pages_base["Torseurs_voiles"],
                    list_cdc=["3 (CQC)", "4 (CQC)"])

with st.expander("Effort dans les voiles intérieurs"):
    "df_efforts_voiles_rupt"
    st.dataframe(df_efforts_voiles_rupt)
    "df_efforts_voiles_base"
    st.dataframe(df_efforts_voiles_base)
with st.expander("Ecarts des efforts dans les voiles intérieurs"):
    df_ecart = voiles_V3.calc_ecarts_efforts_voiles(df_efforts_voiles_rupt, df_efforts_voiles_base,list_effort=["Txy_bas", "Txy_haut"])
    st.dataframe(df_ecart)
    fig = px.scatter(df_ecart, x="id", y="ecart_Txy_haut_rel", color="Cas_de_charges", color_discrete_sequence=px.colors.qualitative.G10, 
                     title="Ecart relatif des efforts dans les voiles inétrieurs", size="I_prep")
    fig.update_xaxes(visible=False)
    fig.update_yaxes(range=[-0.55, 1.5])
    st.plotly_chart(fig)





with st.expander("Pondération inertielle des écarts dans les voiles intérieurs"):
    st.subheader("Moyenne par étage")
    df_fin = voiles_V3.analyse_efforts_voiles_etages(df_efforts_voiles_rupt, df_efforts_voiles_base,list_effort=["Txy_bas", "Txy_haut"],)
    st.dataframe(df_fin)

    df = voiles_V3.calc_moy_pond_ecarts_voiles_bat(df_ecart, )
    st.dataframe(df)


