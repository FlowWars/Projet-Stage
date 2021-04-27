import pypyodbc
import datetime
import csv
import sqlite3
import xlrd
import pandas as pd
import unidecode
import correction_des_communes

#-----------------------------------------------------------------------------------------#
#fontions principales:

def IDStructure():
    curSQL.execute("SELECT Id_Recyclerie FROM Organisation WHERE Recyclerie = ?", (RecyclerieNomGDR))
    id_Comm = curSQL.fetchone()
    for row in id_Comm:
        ID_Comm = row

    return ID_Comm

def verifAnnee(MaxDate, annee):
    date = str(annee) + '/01/01'
    if MaxDate > date:
        return date
    else:
        date = str(annee-1) + '/01/01'
        return date

def insertComm():
    curGDR.execute("SELECT Commune, CodePostal, Déchèterie, Apport, Domicile FROM Commune WHERE EnrActif = 1")
    CommuneList = curGDR.fetchall()

    ID_Struc = IDStructure()
    curSQL.execute("SELECT Commune FROM Commune WHERE Id_Recyclerie = ?", (ID_Struc,))
    CommSQL = curSQL.fetchall()
    CommTab = list()
    for row in CommSQL:
        verif = row[0].upper()
        verif = verif.replace("'", "").replace("-", " ")
        CommTab.append(verif)

    for row in CommuneList:
        Commune = row[0].upper()
        Commune = unidecode.unidecode(Commune)
        Commune = Commune.replace("'", "").replace("-", " ")
        Commune = Commune.strip(' ')
        if Commune[:3] == "ST " or Commune[:4] =="STE ":
            Commune = Commune.replace("ST ", "SAINT ").replace("STE ","SAINTE ").replace(" ST ", " SAINT ").replace(" STE ", " SAINTE ")
        CodePostal = row[1]
        Déchet = row[2]
        Apport = row[3]
        Domicile = row[4]
        codePost = str(CodePostal)
        codePost = codePost[:2] + '%'
        curSQL.execute("SELECT Id_Insee FROM Insee WHERE Commune = ? AND Code LIKE ?", (Commune, codePost))
        id_insee = curSQL.fetchone()
        id_insee = str(id_insee)
        id_insee = id_insee.replace("(", "").replace(",", "").replace(")", "")
        if Commune not in CommTab:
            curSQL.execute("INSERT INTO Commune (Commune, Code_postal, Id_Recyclerie, Id_Insee, Apport, Déchèterie, Domicile) VALUES (?,?,?,?,?,?,?)", (Commune, CodePostal, ID_Struc, id_insee, Apport, Déchet, Domicile))

def insertArr():
    ID_Orga = IDStructure()

    annee = datetime.date.today().year
    curGDR.execute("select max(to_char(Date,'YYYY/MM/DD')) from arrivage")
    MaxDate = curGDR.fetchone()[0]

    date = verifAnnee(MaxDate, annee)

    curSQL.execute("SELECT Id_Commune,Commune FROM Commune WHERE Id_Recyclerie = ?", (ID_Orga,))
    CommSQL = curSQL.fetchall()
    CommTab = {}
    for row in CommSQL:
        CommTab[row[1]] = row[0]

    curSQL.execute("SELECT Id_Tournée, Tournée FROM Tournée WHERE Id_recyclerie = ?", (ID_Orga,))
    TournéeSQL = curSQL.fetchall()
    TournéeDic = {}
    for row in TournéeSQL:
        TournéeDic[row[1]] = row[0]

    curSQL.execute("SELECT max(Id_Arrivage) FROM Arrivage")
    test=curSQL.fetchone() [0]

    curGDR.execute("SELECT to_char(Date,'DD/MM/YYYY'), Origine, Poids_total, Tournée.Intitulé, IDArrivage FROM Arrivage, Tournée WHERE IDCommune = 0 AND Tournée.IDTournée = Arrivage.IDTournée AND date <= %s " %\
            (date))
    ArrivList2 = curGDR.fetchall()
    for row in ArrivList2:
        Date = row[0]
        orig = row[1]
        poids = row[2]
        tournée = row[3]
        tournée = tournée.replace("'", "").replace("-", " ")
        ID_tour = TournéeDic[tournée]
        if not test:
            Id_arr = row[4]
        else:
            Id_arr = test + row[4]
        curSQL.execute("INSERT INTO Arrivage (Id_arrivage, Date, Id_commune, origine, poids_total, Id_recyclerie, Id_tournée) VALUES (?,?,?,?,?,?,?)", (Id_arr, Date, 0, orig, poids, ID_Orga, ID_tour))

    curGDR.execute("SELECT to_char(Date,'DD/MM/YYYY'), Origine, Poids_total, Commune.Commune, IDArrivage FROM Arrivage, Commune WHERE Commune.IDCommune = Arrivage.IDCommune AND date <= %s " %\
            (date))
    ArrivList = curGDR.fetchall()
    for row in ArrivList:
        Date = row[0]
        orig = row[1]
        poids = row[2]
        Comm = row[3]
        Comm = Comm.upper().replace("'","").replace("-"," ")
        Comm = unidecode.unidecode(Comm)
        Comm = Comm.strip(' ')
        ID_comm = CommTab[Comm]
        if not test:
            Id_arr = row[4]
        else:
            Id_arr = test + row[4]
        curSQL.execute("INSERT INTO Arrivage (Id_arrivage, Date, Id_commune, origine, poids_total, Id_recyclerie, Id_tournée) VALUES (?,?,?,?,?,?,?)", (Id_arr, Date, ID_comm, orig, poids, ID_Orga, 0))

def InsertProduit():
    ID_Struc = IDStructure()

    curGDR.execute('SELECT Produit.Nombre, Produit.Poids, Flux.Flux, Etat_produit.Désignation, Categorie.Désignation, Produit.IDArrivage FROM Flux, Produit, Etat_produit, Categorie WHERE Produit.IDFlux = Flux.IDFlux AND Etat_produit.IDEtat_produit = Produit.IDEtat_produit AND Produit.IDCatégorie = Categorie.IDCatégorie')
    List = curGDR.fetchall()

    curSQL.execute("SELECT max(Id_Arrivage) FROM Produit")
    test=curSQL.fetchone() [0]
    for row in List:
        Nombre = row[0]
        Poids = row[1]
        Flux = row[2]
        Flux = Flux.upper().replace("'", "").replace("-", "").replace("/", "").replace(" ", "")
        IDFlux = flux(Flux)
        Orient = row[3]
        Categorie = row[4]
        Categorie = Categorie.upper().replace("'", "").replace("-", "").replace("/", "").replace(" ", "")
        IDCat = cat(Categorie)
        if not test:
            ID_arr = row[5]
        else:
            ID_arr = test + row[5]
        curSQL.execute('INSERT INTO Produit (Orientation, Id_catégorie, Id_Flux, nombre, Id_recyclerie, Poids, Id_arrivage) VALUES (?,?,?,?,?,?,?)', (Orient, IDCat, IDFlux, Nombre, ID_Struc, Poids, ID_arr))

def InsertTournee():
    ID_Struc = IDStructure()

    curGDR.execute('SELECT Intitulé FROM Tournee')
    List = curGDR.fetchall()

    for row in List:
        Tournee = row[0]
        Tournee = Tournee.replace("'", "").replace("-"," ")
        curSQL.execute('INSERT INTO Tournée (Tournée, Id_recyclerie) VALUES (?,?)', (Tournee, ID_Struc))
          
def InsertVente():
    ID_Struc=IDStructure()
    
    annee = datetime.date.today().year
    curGDR.execute("SELECT MAX(to_char(Date,'YYYY/MM/DD')) FROM vente_magasin")
    MaxDate = curGDR.fetchone()[0]

    date = verifAnnee(MaxDate, annee)

    curGDR.execute("SELECT to_char(date,'DD/MM/YYYY'),code_postal,ville,montant_total,tauxremise from vente_magasin WHERE date <= %s " %\
            (date))
    b = curGDR.fetchall()
    for venteorigine in b :
        ville=venteorigine[2].replace("-", " ")
        ville = unidecode.unidecode(ville).upper()
        ville = ville.replace(" ST ", " SAINT ").replace(" STE ", " SAINTE ")
        ville = ville.strip(' ')
        if ville.find("'") :
            ville=ville.replace("'"," ")
        if ville[:3] == "ST " or ville[:4] =="STE ":
            ville = ville.replace("ST ", "SAINT ").replace("STE ","SAINTE ")
        IdInsee = Ville(ville)
        curSQL.execute("INSERT INTO Vente (Id_insee, Date, Code_Postal, Commune, Montant_total, TauxRemise, Id_recyclerie) VALUES('%s', '%s','%s','%s','%s','%s','%s') " %\
                    (IdInsee,venteorigine[0],venteorigine[1],ville,venteorigine[3],venteorigine[4], ID_Struc))
        curSQL.execute("SELECT max(Id_vente) FROM Vente")
        venteoriginemax=curSQL.fetchone() [0]
        curGDR.execute("SELECT Categorie.Désignation,lignes_vente.montant,lignes_vente.poids,lignes_vente.tauxtva,lignes_vente.montanttva, Flux.Flux FROM lignes_vente, Sous_Categorie, Flux, Categorie WHERE idvente_magasin = '%s' AND lignes_vente.IDSous_Catégorie = Sous_Categorie.IDSous_Catégorie AND Sous_Categorie.IDFlux = Flux.IDFlux AND Categorie.IDCatégorie = Lignes_Vente.IDCatégorie" %\
                    (venteoriginemax))
        c=curGDR.fetchall()
        for lignevente in c :
            Categorie = lignevente[0]
            Categorie = Categorie.upper().replace("'", "").replace("-", "").replace("/", "").replace(" ", "")
            IDCat = cat(Categorie)
            Flux = lignevente[5]
            Flux = Flux.upper().replace("'", "").replace("-", "").replace("/", "").replace(" ", "")
            IDFlux = flux(Flux)
            curSQL.execute("INSERT INTO Lignes_vente (Id_catégorie,Montant,Poids,Taux_tva,Montant_tva,Id_vente, Id_Flux) values ('%s','%s','%s','%s','%s','%s','%s')" %\
                        (IDCat,lignevente[1],lignevente[2],lignevente[3],lignevente[4],venteoriginemax, IDFlux))  

def Ville(ville):

    ville = ville.upper().replace("-", " ").replace("'", "")
    ville = unidecode.unidecode(ville)
    curSQL.execute("SELECT Id_Insee, Commune FROM Insee")
    insee = curSQL.fetchall()
    for row in insee:
        if ville == row[1]:
            IdInsee = row[0]
            break
        else:
            IdInsee = 0

    return IdInsee

def catDico():
    test=csv.reader(open('catégorie.csv', "r", encoding='latin-1'), delimiter=',')
    next(test, None)
    MotClé = {}

    for row in test:
        MotClé[row[0]] = row[1]

    return MotClé

def fluxDico():
    test=csv.reader(open('flux.csv', "r", encoding='latin-1'), delimiter=',')
    next(test, None)
    MotClé = {}

    for row in test:
        MotClé[row[0]] = row[1]

    return MotClé

def cat(cat):
    
    MotClé = catDico()

    IDCat = 12
    for mot, Id in MotClé.items():
        if cat.find(mot) != -1:
            IDCat = Id
            break
        else:
            continue

    return IDCat

def flux(flux):
    MotClé = fluxDico()

    IDFlux = 1
    for mot, Id in MotClé.items():
        if flux.find(mot) != -1:
            IDFlux = Id
            break
        else:
            continue

    return IDFlux

def remplacement(mot):
    mot = mot.replace("'", "\\")
    return (mot)

def date():
    jourj = datetime.date.today()
    annuel = jourj - datetime.timedelta(days=366)
    annuel = str(annuel)
    annuel = annuel.replace("-","")

def correct():
    curGDR.execute("SELECT Ville FROM Organisation")
    Ville = curGDR.fetchone()
    Ville = Ville[0].upper().replace("-"," ").replace("'", "")
    curSQL.execute("SELECT Longitude, Latitude FROM Insee WHERE Commune = ?", (Ville,))
    GPS = curSQL.fetchone()
    ID = IDStructure()
    correction_des_communes.correction(connect, curSQL, ID, GPS[0], GPS[1])

#--------------------------------------------------------------------------------------------------------------
# Code principal

print("connexion en cours à la base de la recyclerie à extraire")
conn = pypyodbc.connect(DSN='Extraction')  # initialisation de la connexion au serveur
curGDR = conn.cursor()
print("connexion ok\n")

print("connexion en cours à la grosse base de données")
connect = sqlite3.connect("finale.db")
curSQL = connect.cursor()
print("connexion ok\n")

#######################################################################
##INSERTION DES DONNEES##
try:
    curGDR.execute("SELECT RaisonSociale FROM Organisation")
    RecyclerieNomGDR = curGDR.fetchone()

    curSQL.execute("INSERT OR IGNORE INTO Organisation (Recyclerie) VALUES (?) ", (RecyclerieNomGDR))

    print("Insertion en cours...")
    #InsertTournee()
    print("Tournée insérée")
    #insertComm()
    print("Commune insérée")
    #correct()
    #insertArr()
    print("Arrivage inséré")
    #InsertProduit()
    print("Produit inséré")
    #InsertVente()
    print("Vente inséré")

    #requete pour les sous categorie
    #curGDR.execute("SELECT SUM(ROUND((sous_categorie.Poids_Moyen*Lignes_vente.nombre),2)) FROM Lignes_vente INNER JOIN sous_categorie ON Lignes_vente.IDSous_Catégorie = Sous_Categorie.IDSous_Catégorie WHERE IDvente_magasin IN ( SELECT distinct(vente_magasin.idvente_magasin) FROM vente_magasin INNER JOIN Lignes_vente ON vente_magasin.idvente_magasin = lignes_vente.idvente_magasin   )  and lignes_vente.poids =0") 

    #connect.commit()
    print("insertion des données effectué")
except:
    print("erreur")

connect.close()
conn.close()
curGDR.close()

