# Le Tremplin

Veille emploi : Product, Ops, IA et No-Code, remote depuis la France et français accepté.

## Publication

Vercel publie la branche main. Le workflow `.github/workflows/publier.yml` est prévu le lundi à 9 h Europe/Paris et peut être lancé manuellement, avec test_mode activé par défaut.

Ajouter le secret GitHub Actions `OPENAI_API_KEY` avant tout test. La clé du Signal ne se transmet pas automatiquement à ce dépôt. L’API est facturée séparément de ChatGPT.

Le générateur recherche sur le web, exclut les URL et titres du registre `data/annonces.json`, produit une édition datée et conserve les archives. Les résultats automatiques restent à confirmer sur les annonces. Aucune candidature ou prise de contact automatique. Ce workflow ne met pas à jour Airtable et n’envoie pas d’e-mail.

Lancer d’abord un test manuel puis contrôler l’artifact HTML. Le secret et un test réussi sont nécessaires avant de considérer l’automatisation opérationnelle.
