# Administrateur PC 2025-2026

**⚠️ Prérequis :** Vous devez être connectés via vos identifiants région.

---

## 1 - 2

Eteindre votre pc
le demarrer
Des que le logo / rond de chargement apparait : forcer l'arret avec le bouton éteindre (le maintenir pour qu'il s'arrete)
recommencer 2-3 fois, jusqu'a ce que vous voyez "veuillez patienter"
Dans le menu de recupération ou de reparation (option avancé) : Dépannage → Options avancées → Invite de commandes

## CELA PEUT DEMANDER PLUSIEURS TENTATIVES / REDEMARRAGE, C'EST ALEATOIRE IL FAUT ETRE PATIENT

---

**🔸 3️⃣ Identifier la lettre du disque système**

Tapez :

```
C:
```

- Si le chemin affiché devient `C:\>`, vous êtes sur le bon disque.

---

**🔸 4️⃣ Sauvegarder et remplacer utilman.exe**

Toujours dans l'invite de commandes, tapez :

```
cd Windows\System32
```

```
move utilman.exe utilman.old
```

```
copy cmd.exe utilman.exe
```

_(Ces commandes sauvegardent l'original et le remplacent par `cmd.exe`.)_

---

**🔸 5️⃣ Redémarrer**

- Fermez la fenêtre.
- Cliquez sur **Continuer → Quitter et passer à Windows 10/11**.

---

**🔹 6️⃣ Créer un compte administrateur**

1. À l'écran de connexion, cliquez sur **Options d'ergonomie** (icône en bas à droite) ou utilisez **Win + U**.
2. Une **Invite de commandes** s'ouvre en mode SYSTEM.
3. Tapez ces commandes une par une :

```
net user LocalAdmin /del
```

```
net user LocalAdmin votremdp /add
```

```
net localgroup Administrateurs LocalAdmin /add
```

_(Le nom `LocalAdmin` est fortement conseillé.)_ **Si la fenêtre se ferme seule** : Spammez **Win + U** jusqu'à ce qu'elle reste ouverte.

---

**🔹 7️⃣ Vérification et sécurisation**

1. Connectez-vous à votre session Windows.
2. Ouvrez **PowerShell** (recherchez → clic droit → _Exécuter en tant qu'administrateur_).
3. Dans la fenetre qui s'ouvre, entrez :
   - **Nom d'utilisateur** : `.\LocalAdmin`
   - **Mot de passe** : _(votremdp)_
4. Tapez :

```
lusrmgr.msc
```

5. Allez dans **Utilisateurs** → double-cliquez sur `LocalAdmin`.
6. Cochez **« Le mot de passe n'expire jamais »** → **Appliquez** → **OK**.

---

**🔹 8️⃣ Utiliser le compte comme administrateur**

1. Ouvrez le **Panneau de configuration**.
2. Allez dans : `Comptes d'utilisateurs > Comptes d'utilisateurs > Modifier le type de compte`
3. Si demandé, entrez :
   - **Nom d'utilisateur** : `.\LocalAdmin`
   - **Mot de passe** : _(laissez vide sauf si vous avez mis un mdp)_
4. Cliquez sur **Oui** → sélectionnez **Administrateur** → **Modifier le type de compte**.
5. Redémarrez le PC.

### 🛡️ 9️⃣ : BLOQUER LE RETOUR EN ARRIÈRE (IME SCRIPTS)

1. Allez dans : `C:\Windows\IME-cache\HealthScripts`
2. Ouvrez les dossiers présents. Pour **CHAQUE fichier** à l'intérieur :
3. Clic droit → **Ouvrir avec le Bloc-notes**.
4. **Supprimez tout le texte** à l'intérieur du fichier.
5. **Enregistrez** le fichier vide.

*(Le script de la région ne pourra plus s'exécuter pour vous retirer vos droits !)*

---

**🔒 Optionnel mais recommandé : Activer BitLocker pour chiffrer votre disque**

*Protégez vos données contre le vol ou l'accès non autorisé.*

---

### 🔧 Étapes pour activer BitLocker

**1️⃣ Ouvrir BitLocker**

Appuyez sur **`Win + S`**, tapez :

```
bitlocker
```

→ Sélectionnez **`Gérer BitLocker`**

---

**2️⃣ Activer BitLocker**

Cliquez sur :

```
Activer BitLocker
```

*(Sur le lecteur `C:`)*

---

**3️⃣ Choisir un mode de déverrouillage**

Sélectionnez :

```
Utiliser un mot de passe
```

→ Entrez un **mot de passe complexe** (12+ caractères)

---

**4️⃣ Sauvegarder votre clé de récupération**

**⚠️ CRITIQUE** : Choisissez une option :

```
Compte Microsoft / Fichier / Impression
```

*(Sans cette clé, vos données seront **perdues** en cas de problème !)*

---

**5️⃣ Options de chiffrement**

Sélectionnez :

```
Chiffrer tout le lecteur
Nouveau mode de chiffrement
```

---

**6️⃣ Lancer le chiffrement**

Pensez à vous connecter une première fois puis utilisez ``win + l`` ou verrouiller la session (pas vous déconnecter !), avant d'effectuer les commandes

Cliquez sur :

```
Démarrer le chiffrement
```

*(Processus long, ne pas interrompre !)*

---

**7️⃣ Redémarrer si nécessaire**

Windows peut demander un redémarrage.

---

### 🔍 Vérification

Retournez dans **`Gérer BitLocker`** :

→ Le lecteur `C:` doit afficher **`Chiffrement activé`**
→ Testez le déverrouillage avec votre mot de passe/clé USB

### ⚠️ Conseils de sécurité

- **Ne perdez JAMAIS votre clé de récupération**
- Évitez de désactiver BitLocker sans sauvegarde
- Sur SSD, impact minime sur les performances

---

# Administrateur PC sans clé BitLocker

# ***En utilisant ce tutoriel, vous certifiez avoir lu et accepté les conditions d'utilisation (voir tout en bas)***

# Ce tuto fonctionne **uniquement** pour windows 11 !

**Une souris est recommandée (non obligatoire) pour ce tutoriel**

## ⚙️ Préparation de l'installation

### 1️⃣ Branchement et téléchargement

- **Branchez** votre PC tout au long de l'opération.
- **Téléchargez** la version de Windows de votre choix via ce lien : [Windows ISO](https://pcpdl.eu/liens-utiles/).
- **Formatez** votre **clé USB** au format **NTFS**. (clic droit sur votre clé, formater)
- **Ouvrez** le fichier ISO en double-cliquant dessus.
- **Sélectionnez** tous les fichiers, **copiez-les**, puis **collez-les** sur votre **clé USB**.
- **Ajoutez également ce fichier** : [wifi](https://pcpdl.eu/liens-utiles/) sur la clé USB. (sauf si vous avez un câble ethernet)

## 🔄 Démarrage et installation

### 2️⃣ Accéder au menu de dépannage

Eteindre votre pc
le demarrer
Des que le logo / rond de chargement apparait : forcer l'arret avec le bouton éteindre (le maintenir pour qu'il s'arrete)
recommencer 2-3 fois, jusqu'a ce que vous voyez "veuillez patienter"
Dans le menu de recupération ou de reparation (option avancé) : Dépannage → Options avancées → Recuperation de l'image systeme

## CELA PEUT DEMANDER PLUSIEURS TENTATIVES / REDEMARRAGE, C'EST ALEATOIRE IL FAUT ETRE PATIENT

### 3️⃣ Lancer l'installation

- Une **fenêtre d'installation de Windows** s'ouvrira, **fermez-la**.
- **Cliquez sur** :
  1. `Suivant`
  2. `Avancé`
  3. `Installer un pilote`
  4. `OK`
- **Un explorateur de fichiers s'ouvrira**.
- **Accédez à votre clé USB**, cliquez **droit** sur le fichier `setup`, puis **Executer**.

  ⚠️ *Si le fichier setup n'apparaît pas* :
  📌 **Écrivez** `*.*` dans la barre "Nom du fichier", puis validez.

## 🖥️ Installation de Windows

### 4️⃣ Choisir et installer Windows

- **Vérifiez la langue**, puis cliquez sur `Suivant`.
- **Cliquez sur** `Installer maintenant`.
- **Sélectionnez** la version de Windows souhaitée.
- **Cliquez sur** `Je n'ai pas de clé de produit` (*choisissez la version **Professionnelle** recommandée*).
- **Cliquez sur** :
  🔹 `Suivant` → `Personnalisé : Installer uniquement Windows`
- **Supprimez toutes les partitions**, sauf la **partition de récupération** et **votre clé USB !**. ( A partir d'ici ne plus éteindre votre pc !)
- **Cliquez sur** `Nouveau` → `OK` → `Suivant`.

### 5️⃣ Finalisation de l'installation

- L'installation commencera et le PC redémarrera.
- **À la fin de l'installation**, utilisez la touche `Shift` pour naviguer dans les options.

---

## 🔑 Création d'un compte administrateur

### 6️⃣ Activer le compte administrateur

- **Sur l'écran de connexion Internet**, **maintenez** `Shift` et appuyez sur `F10` pour ouvrir une fenêtre de commande.
- **Tapez** la commande suivante et appuyez sur `Entrée` :

```bash
net user administrateur /active:yes
```

- **Ajoutez un nouvel utilisateur** :

```bash
net user /add username password
```

Remplacez `username` par le nom d'utilisateur de votre choix (**sans espace**).
Remplacez `password` par le mot de passe souhaité (**sans espace**).

📌 *Pour afficher un nom complet* :
Ajoutez `/fullname:"Prénom Nom"` après `password`.

- **Ajoutez l'utilisateur aux administrateurs** :

```bash
net localgroup administrateurs username /add
```

(*Si Windows est en anglais, remplacez `administrateur` par `administrator` et `administrateurs` par `administrators`*).

### 📶 Installer le pilote Wi-Fi (sauf si vous avez un câble ethernet)

1. Tapez :

   ```bash
   explorer.exe
   ```

   Une fenêtre d'explorateur Windows s'ouvrira.

2. Allez dans la clé USB et ouvrez `sp150721.exe`, installez-le et attendez quelques instants.

## Le wifi sera disponible.

3. Revenez sur l'invite de commandes et tapez :

   ```bash
   cd oobe
   ```

   Appuyez sur `Entrée`.

4. Tapez ensuite :

   ```bash
   msoobe.exe
   ```

   Puis appuyez sur `Entrée`.

📌 Votre PC affichera "Veuillez patienter...". Attendez **30 secondes**, même si le message persiste.

🔴 *Forcer l'arrêt de l'ordinateur* : Maintenez le bouton d'alimentation enfoncé.

5. **Redémarrez** votre PC et connectez-vous avec le compte créé.

---

### ❌ Retirer le compte administrateur de la connexion

Ouvrez une invite de commande en tant qu'administrateur et tapez :

```bash
net user administrateur /active:no
```

### Connectez vous a un reseau wifi, et faites les mises a jours windows !

https://www.microsoft.com/fr-fr/software-download/windows11

(lien temporaire pour avoir l'iso de windows 11)

---

# Administrateur au premier démarrage

### 📜 En utilisant ce tutoriel, vous certifiez avoir lu et accepté les conditions d'utilisation ci-dessus.

**⚠️ Veuillez suivre attentivement les étapes suivantes. Si vous commettez des erreurs, cela ne sera pas de notre responsabilité, veuillez donc vérifier que vous avez bien tout recopié correctement.
Pensez bien à le lire dans son __intégralité__ avant de commencer.**

---

## 🛠️ Étapes à suivre

1️⃣ **Sur la page de demande de l'e-mail**, **maintenez** la touche **Majuscule/Shift** et **appuyez sur F10**.
   📌 Cela ouvrira une **fenêtre de commande**.

2️⃣ **Dans cette fenêtre, tapez** :

   ```cmd
   net user administrateur /active:yes
   ```

   ⏩ **Puis appuyez sur Entrée.**

3️⃣ **Tapez ensuite** :

   ```cmd
   net user /add username password
   ```

   🔹 Vous devrez **remplacer** `username` par le **nom d'utilisateur** de votre choix **(sans espace)**.
   🔹 **Remplacez** `password` par le **mot de passe** souhaité **(sans espace)**.

   📌 **Optionnel** :
   Si vous souhaitez **ajouter votre prénom et nom** dans les affichages, vous pouvez ajouter un **espace**, puis :

   ```cmd
   /fullname:"Prénom Nom"
   ```

   Exemple :

   ```cmd
   net user /add JohnDoe Password123 /fullname:"John Doe"
   ```

   ✅ **Appuyez sur Entrée.**

4️⃣ **Ajoutez l'utilisateur au groupe Administrateurs** :

   ```cmd
   net localgroup administrateurs username /add
   ```

   📌 **Remplacez "username" par le même nom d'utilisateur que précédemment.**

   ⚠ **Si votre installation est en anglais**, vous devez remplacer :
   - `administrateur` ➡ `administrator`
   - `administrateurs` ➡ `administrators`

5️⃣ **Tapez** :

   ```cmd
   cd oobe
   ```

   ✅ **Appuyez sur Entrée.**

6️⃣ **Exécutez la commande suivante** :

   ```cmd
   msoobe.exe
   ```

   ✅ **Appuyez sur Entrée.**

7️⃣ **Votre ordinateur affichera "Veuillez patienter...".**
   ⏳ **Attendez 30 secondes**

8️⃣ Même si le message **"Veuillez patienter..."** est toujours affiché, **forcez l'arrêt** de votre ordinateur en **maintenant le bouton d'allumage enfoncé**.

9️⃣ **Une fois votre ordinateur éteint, rallumez-le.**

🔟 **Votre ordinateur est maintenant déverrouillé.**
   Vous pouvez vous connecter en utilisant le **compte que vous avez créé**.

---

### ❌ Retirer le compte administrateur de la connexion

Ouvrez une invite de commande en tant qu'administrateur et tapez :

```bash
net user administrateur /active:no
```

## 🎁 Bonus

💡 **En débridant votre ordinateur, vous avez maintenant les permissions administrateur sur votre compte.**

⚠ **Note importante** :
Les créateurs de ce tutoriel **ne sont pas affiliés** à **la région Pays de la Loire, Windows, HP ou Microsoft**.
Ils **ne peuvent être tenus responsables** en cas de dommages causés par une mauvaise utilisation de ce tutoriel.

---

# Administrateur sous la région

Comment être administrateur sous le système de la région ?

## Devenir administrateur sur un PC de la région (sous la région)

*Pour les pc sous windows 11, aller directement a l'étape 2 sauter l'étape 4, puis continuer le tuto normalement. (ne pas tenir compte des prérequis)*

> **⚠️ Prérequis :** Etre sur la page de demande d'email de la région. ( Possible avec <#1072932101034356757> sans le suivre jusqu'au bout.)

---

## 🔎 Vérification de BitLocker

Appuyez sur `Shift + F10` pour ouvrir une invite de commandes.
Tapez :

```
manage-bde -status
```

Si BitLocker est activé, tapez :

```
manage-bde -off C:
```

Puis attendez la désactivation complète.

---

## 🧩 Partie 1 – Créer un compte admin à part (`compteadmin`)

### 🥇 Étape 1 : Créer un compte temporaire

```
net user 123 abc /add
```

```
net localgroup administrateurs 123 /add
```

### 🔁 Étape 2 : Redémarrer en mode récupération

```
shutdown /r /o /t 0
```

### 🔧 Étape 3 : Remplacer `utilman.exe` par `cmd.exe`

Une fois dans l'environnement de récupération :

> **Chemin :** Dépannage → Options avancées → Invite de commandes
> **Connexion :** Utilisez `123` / `abc` si demandé

Tapez :

```
C:
```

```
cd Windows\system32
```

```
copy utilman.exe utilmanold.exe
```

```
copy cmd.exe utilman.exe
```

Ecrire "o" pour confirmer.

### 🗑️ Étape 4 : Supprimer le compte temporaire

Depuis l'écran de connexion (`Shift + F10`) :

```
net user 123 /del
```

### Étape 5 : Créer le compte `compteadmin`

1. Connectez-vous à votre session région
2. Appuyez sur `Win + L` pour revenir à l'écran de verrouillage
3. Appuyez sur `Win + U`
   - Si la fenêtre CMD s'ouvre puis se ferme direct :
     **Spammer `Win + U`**, même si plusieurs fenêtres apparaissent.

Dans la fenêtre qui s'ouvre :

```
net user compteadmin /add
```

```
net localgroup administrateurs compteadmin /add
```

- Si `compteadmin` est **déjà créé**, tapez :

```
net user compteadmin *
```

Ne mettez pas de mot de passe (faites juste entrer)

> 🔐 **compteadmin** est sans mot de passe

### ✅ Étape 6 : Vérifier l'accès administrateur

1. Connectez-vous à votre session région
2. Cherchez "cmd" → clic droit → *Exécuter en tant qu'administrateur*
3. Entrez :
   - **Nom d'utilisateur :** `.\compteadmin`
   - **Mot de passe :** *(laisser vide)*

### 🛡️ Étape 7 : Mot de passe permanent

1. Rechercher "Gestion de l'ordinateur", lancer en administrateur
2. Aller dans : **Utilisateurs locaux et groupes > Utilisateurs**
3. Double-cliquez sur `compteadmin`
4. Cochez **"Le mot de passe n'expire jamais"**
5. Cliquez sur **Appliquer**, puis **OK**

---

## 🔄 Partie 2 – Utiliser le compte région comme administrateur (pas de création)

1. Ouvrir le **Panneau de configuration**
2. Aller dans :
   `Comptes d'utilisateurs > Comptes d'utilisateurs > Modifier votre type de compte`
3. À la demande d'identifiants administrateur :
   - **Nom :** `.\compteadmin`
   - **Mot de passe :** *(laisser vide)*
4. Cliquez sur **Oui**
5. Sélectionnez **Administrateur** puis **Modifier le type de compte**
6. Redémarrez le PC

---

## ⚠️ Infos Importantes

- **❌ Ne vous connectez JAMAIS** directement au compte `compteadmin`.
  → Cela supprimera la session du lycée de l'écran de connexion.

---

# Revenir sous la région

## Si jamais vous rencontrez des problèmes, vous pouvez à tout moment revenir sur le système de la région.

- Si votre PC n'est pas modifié : faites en sorte de faire le tutoriel <#1072932101034356757>, et lorsque vous êtes à l'étape du choix du réseau (Wifi ou Ethernet), choisissez votre réseau et cliquez sur Suivant, et patientez un peu.
  Si vous voyez un texte comme « ***Bienvenue chez Conseil Régional des Pays de la Loire – Direction des Lycées !*** » ou un logo ressemblant à celui des Pays de la Loire, il vous suffit de mettre votre adresse email de la région **(prenom.nom@[RNE/UAI DE VOTRE LYCEE].paysdelaloire.education)**, puis votre mot de passe.

- Si votre PC est modifié (et que vous avez bien tout configuré sur les permissions **__Administrateur__**) : il vous suffit de faire `Win + R`, tapez « **sysprep** » et faites Entrée.
  Sur "l'action de nettoyage du système", vérifiez qu'il s'agit de « **Entrer en mode OOBE (Out-Of-Box Experience)** » et vérifiez bien que l'option d'extinction est « **Redémarrer** » puis faites « **OK** ». Patientez, et faites les étapes inscrites à l'écran.
  Si le **`sysprep`** ne marche pas, faites l'étape du PC non-modifié.

> **__Votre fenêtre doit être configurée de la même manière que sur la photo disponible a cette adresse: https://discord.com/channels/1072925050409324644/1140219251379146873/1209913275945590864 .__**

---

# Activation Office

## Activation d'Office sans email scolaire

> ⚠️ **Avertissement** : Pour commencer ce tutoriel, veuillez avoir installé la dernière version d'Office (Office 2021).

## Etape 1

Appuyez sur `Win + R` sur votre clavier. La boîte de dialogue **Exécuter** s'ouvrira.
Ensuite, saisissez `PowerShell` et appuyez sur la combinaison de touches `Ctrl + Shift + Entrée`.

## Etape 2

Dans Powershell, tappez la commande ci dessous :

```powershell
irm  https://get.activated.win | iex
```

puis appuyez sur Entrée.

## Etape 3

Une deuxième fenêtre vient de s'ouvrir, veuillez entrer d'abord le numéro 2, puis le numéro 1.

## Fin du tutoriel

Veuillez patienter jusqu'à ce que le chargement se termine, puis fermer la page.

*Ecrit par Myuui.*

---

# Installation d'une app sans Bitlocker

**Il existe plusieurs moyens d'installer de logiciels et applications du Microsoft Store**

**1 : Pour les applications du Microsoft Store**

- aller sur https://apps.microsoft.com/home?hl=fr-fr&gl=FR
- chercher sur le site l'application que vous voulez télécharger
- lorsque vous êtes sur la page de l'application si il y a un bouton "Télécharger" appuyer dessus et une fois le téléchargement terminé ouvrir le fichier et cliquer sur installer et l'application sera installée. Si il n'y a pas ce bouton, copier le lien de cette page.
- aller sur https://store.rg-adguard.net/, coller le lien et cliquer sur ✅
- cliquer sur le lien contenant le nom de votre application et finissant par .appx ou .appxbundle ou .msixbundle. Si il y en a plusieurs comparer les versions que vous voyez dans le nom du lien.
- une alerte de sécurité bloquera le téléchargement selon votre navigateur vous devrez cliquer sur "autoriser le téléchargement" ou "enregistrer" ou clic droit puis "conserver"
- ouvrez le ficher téléchargé et cliquez sur installer

**2 : Pour certains logiciels**

- télécharger le fichier d'installation du logiciel
- créer un dossier dans les téléchargements et déplacer le fichier d'installation dedans
- faire clic droit sur le fichier d'installation puis cliquer sur 7zip puis sur extraire ici
- des fichiers vont apparaitre. ouvrir le fichier contenant le nom du logiciel
- le logiciel fonctionne. Si il ne fonctionne pas et que vous avez essayé la méthode 2 c'est qu'il n'est pas possible d'installer ce logiciel
- si le logiciel fonctionne, ne jamais supprimer le dossier que vous avez créé. Pour ouvrir ce logiciel il faudra aller dans ce dossier et ouvrir le fichier contenant le nom du logiciel

**3 : Pour certains logiciels**

- Télécharger le fichier d'installation du logiciel
- Télécharger la pièce jointe disponible a cette adresse: https://discord.com/channels/1072925050409324644/1350199494792183879/1350200628197982293
- Glisser le fichier d'installation sur ce fichier
- l'installation va se lancer. Si ça ne marche pas essayer la méthode 2

---

# Changer de fond d'écran

## Changer le fond d'écran de verrouillage sur les PC de la région.

👇👇

**Pré-requis : Être Administrateurs avec la region.**

- Allez dans le dossier `C:\ProgramData\LockScreenImage`
- Copier le nom de l'image et le donner à l'image de votre choix
- Copier votre image et écraser l'ancienne

***Vous pouvez désormais à tout moment changer cette image et lui donner le nom de celle déjà présente.***

*Diaporama d'images impossible*

Merci à <@1221839347633098762> pour ce tuto

---

# Acceder au mstore

***Info : Le tuto ne fonctionne pas sur les PC 2025-2026***

**1 :** Téléchargez le fichier **[Ici](https://discord.com/channels/1072925050409324644/1499731253522468996/1499736161080447157)**

**2 :** Le mettre dans le dossier suivant :

Touche Windows + R et tapez --> `shell:startup` (ouvre le dossier direct)

👇👇👇

Dossier : `C:\Users\NOM_USER\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`

**Info accès au dossier manuellement :** Remplacez `NOM_USER` par votre nom d'utilisateur.

Exemple avec quelqu'un qui s'appelle Pierre Michelin :

`C:\Users\PIERRE.MICHELIN\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`

---

**Comment fonctionne le script :**
Il vérifie la/les valeur(s) du registre qui bloque le Microsoft Store
Si 1 alors il remet à 0, si 0 alors revérifie toutes les 10min indéfiniment

**3 :** Rendre le déblocage actif

**Redémarrer le PC ou ouvrez le fichier `.exe`**

*Nous avons eu des retours comme quoi ce tuto ne fonctionnait pas pour certains d'entre vous, si c'est le cas vérifiez que vous êtes sous Windows 11 24H2 (besoin d'aide pour vérifier ? --> <#1072925050967171215> )*

---

# Mot de passe BIOS

## Mot de passe Accès BIOS

**__G8 (PC 2021-2022) :__** ci5Z7mKU97

**__G9 (PC 1ère génération 2022-2023) :__** 1pvFXs2i5l (changé sur la plupart des pcs maintenant :/) --> 6ZrMe9BrXF

**__G9 (PC 2ème génération 2023-2024) :__** *en cours de recherche*

**__G10 (PC génération 2024-2025) :__** *en cours de recherche*

PS : pour écrire les chiffres il faut utiliser la touche **shift** (flèche du haut) et non la touche **verr.maj**

*(Si vous êtes dans le lycée Aristide Briant principalement mais ça peut arriver dans les autres établissement, il y a des chances que vous ayez reçu un PC HP G9 1ère génération même si vous êtes d'année 2008 pour verifier ça, regardez si vous avez une étiquette HP Wolf Security à coté de l'étiquette Pentium, si vous avez une etiquette, c'est un gen1, sinon non)*

GG <@&1086300669142646844>

> ## ⚠️ Si vous vous connectez à votre compte de la région après avoir déverrouiller votre BIOS, il se rebloquera automatiquement avec un mot de passe différent !