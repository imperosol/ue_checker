# ue_checker

ue_checker est un bot discord qui permet de consulter certaines informations sur le dossier étudiant de l'UTT.

# Commandes

ue_checker possède les commandes suivantes :

- `!register` : permet de s'inscrire auprès du bot. **L'inscription est nécessaire pour utiliser les autres commandes**. Le bot va alors demander par message privé les identifiants et les enregistrer. Les identifiants stockés sur la base de données sont cryptés. Si des informations erronées sont données au bot, il faut se désinscrire et recommencer.
- `!unregister` : permet de se désinscrire. Toutes les informations personnelles sont supprimées de la base de données. L'utilisation des commandes du bot n'est alors plus possible.
- `!get_decision [args]` : permet de consulter l'avis du jury sur un semestre en particulier. Les noms des semestres doivent être marqués sans le '0' (TC1 au lieu de TC01). Si un semestre a été annulé, le deuxième semestre est accessible en ajoutant (1) (Si le TC3 est annulé, le deuxième TC3 s'appellera TC3(1)). On peut aussi demander tous les semestres, avec `all`, ou seulement le dernier avec `last`. Si aucun argument n'est donné, le bot renvoie le dernier semestre.
- `!get_letters [semestre]` : permet de consulter les lettres obtenues sur un semestre en particulier. Les arguments de la commande sont les mêmes que pour `!get_decision`
- `!cache [durée (en minutes)]` : met le dossier étudiant en cache pendant la durée spécifiée.
Commande très pratique et qui vous fera gagner du temps si vous comptez faire plusieurs traitements sur votre dossier étudiant à la suite.
Si la durée n'est pas spécifiée, le dossier étudiant est mis en cache pour une durée de 5 minutes.
Il n'est pas permis de mettre le dossier en cache pendant une durée supérieure à 10 minutes.
- `!set_cache_life`

# Sécurité des données

L'utilisation du bot implique de confier ses identifiants personnels 
au bot. Ces identifiants sont stockés sur une base de données.

Avant leur insertion en base de données, ils sont cryptés avec une
clef unique accessible uniquement au responsable de ce projet.
Vos données sont donc protégées d'éventuelles actions de personnes
tierces.

Cependant, cela implique également que le responsable du projet, 
*Thomas Girod*, peut accéder à vos données. Vous n'avez pas de raison
de craindre pour vos données, qui ne seront jamais décryptées 
et consultées par un humain, pour quelque raison que ce soit.

Vous ne devez confier vos données qu'en connaissance de cause et
seulement si vous faîtes suffisamment confiance au responsable
du projet pour ça.