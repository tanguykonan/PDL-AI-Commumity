# Base de Connaissances & Tutoriels du Serveur (Exemple)

Ce fichier Markdown sert de modèle de base de connaissances pour le moteur RAG vectoriel (TSE) du bot.
Vous pouvez ajouter autant de sections, tutoriels, guides ou FAQ que vous le souhaitez ci-dessous.
ChromaDB découpera et indexera automatiquement ce texte en vecteurs pour répondre précisément aux questions des membres.

---

## 1. Règles Générales du Serveur

- **Respect et Courtoisie** : Traitez chaque membre avec respect. Aucun propos haineux, discriminatoire ou insultant n'est toléré.
- **Salons Textuels et Vocaux** : Merci de respecter les thématiques des différents salons.
- **Publicité et Spam** : L'auto-promotion et le spam en message public ou privé sont strictement interdits sans autorisation du staff.
- **Signalement** : Pour signaler un comportement abusif, contactez un membre de l'équipe de modération ou utilisez la commande `/help support`.

---

## 2. Commandes et Utilisation du Bot

### Commandes Générales
- `/help` : Affiche le panneau d'aide interactif et les informations du bot.
- `/help support` : Ouvre un formulaire direct pour envoyer une question ou un rapport au support.

### Commandes de Musique (`/music`)
- `/music play <titre ou url>` : Joue une musique ou une playlist dans votre salon vocal.
- `/music pause` : Met en pause la lecture en cours.
- `/music resume` : Reprend la lecture de la musique.
- `/music skip` : Passe à la piste suivante dans la file d'attente.
- `/music stop` : Arrête la musique et déconnecte le bot du salon vocal.
- `/music queue` : Affiche la liste des morceaux en attente.
- `/music volume <1-100>` : Ajuste le volume sonore.

### Commandes de Modération (`/modo`)
- `/modo timeout <membre> <durée> <raison>` : Rend temporairement muet un membre (ex: `10m`, `2h`, `1d`).
- `/modo kick <membre> <raison>` : Expulse un utilisateur du serveur.
- `/modo ban <membre> <raison>` : Bannit un utilisateur du serveur.
- `/modo unban <user_id>` : Lève le bannissement d'un utilisateur.
- `/modo clear <nombre>` : Supprime un nombre spécifique de messages récents dans le salon.

### Commandes d'Administration Serveur (`/staff`)
- `/staff config` : Ouvre le panneau de configuration interactif (changement de langue, mode de personnalité IA, salons autorisés, auto-sanctions).

---

## 3. Foire Aux Questions (FAQ)

### Comment changer la personnalité du bot sur mon serveur ?
Utilisez la commande `/staff config` pour ouvrir le panneau interactif, puis sélectionnez le mode de personnalité souhaité (`default`, `caveman`, `cartman`, etc.) dans le menu déroulant.

### Comment restreindre le bot à certains salons ?
Ouvrez `/staff config` puis rendez-vous dans la section salons pour sélectionner les canaux textuels autorisés.

### Comment ajouter mes propres guides dans cette base de connaissances ?
Il suffit d'éditer ce fichier `settings/resources/strings/tutoriels.md` et d'ajouter vos titres et paragraphes avec la syntaxe Markdown (`# Titre`, `## Sous-titre`, listes à puces). Le bot réindexera automatiquement les informations au démarrage.
