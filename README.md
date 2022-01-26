# ue_checker

ue_checker est un bot discord qui permet de consulter certaines informations sur le dossier étudiant de l'UTT.

# Commandes

ue_checker possède les commandes suivantes :

- `!register` : permet de s'inscrire auprès du bot. *L'inscription est nécessaire pour utiliser les autres commandes*. Le bot va alors demander par message privé les identifiants et les enregistrer. Les identifiants stockés sur la base de données sont cryptés. Si des informations erronées sont données au bot, il faut se désinscrire et recommencer.
- `!unregister` : permet de se désinscrire. Toutes les informations personnelles sont supprimées de la base de données. L'utilisation des commandes du bot n'est alors plus possible.
- `!get_decision <semestre>` : permet de consulter l'avis du jury sur un semestre en particulier. Les noms des semestres doivent être marqués sans le '0' (TC1 au lieu de TC01). Si un semestre a été annulé, le deuxième semestre est accessible en ajoutant (1) (Si le TC3 est annulé, le deuxième TC3 s'appellera TC3(1)). On peut aussi demander tous les semestres, avec `all`, ou seulement le dernier avec `last`. Si aucun argument n'est donné, le bot renvoie le dernier semestre.
- `!get_letters <semestre>` : permet de consulter les lettres obtenues sur un semestre en particulier. Les arguments de la commande sont les mêmes que pour `!get_decision`
