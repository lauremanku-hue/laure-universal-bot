# Laure Bot - Déploiement sur Railway

Ce bot WhatsApp est conçu pour fonctionner sur Railway avec Flask et Neonize.

## Configuration

1.  **Variables d'environnement** :
    *   `GEMINI_API_KEY` : Votre clé API Gemini pour les fonctionnalités IA.
    *   `PORT` : 3000 (Railway le définit automatiquement).

2.  **Stockage Persistant** :
    *   WhatsApp nécessite de sauvegarder une session (`laure_session.db`).
    *   Sur Railway, ajoutez un **Volume** et montez-le sur `/app/data`.
    *   Modifiez le chemin de la session dans `app/modules/whatsapp_web.py` pour pointer vers `/app/data/laure_session.db`.

## Déploiement

Le projet contient un `Dockerfile` et un `Procfile` pour faciliter le déploiement sur Railway.

1.  Connectez votre dépôt GitHub à Railway.
2.  Railway détectera automatiquement le `Dockerfile` ou le `Procfile`.
3.  Vérifiez les logs pour voir le QR code à scanner lors de la première connexion.

## Résolution des problèmes

*   **Timeout / EOF** : Cela arrive souvent si la connexion est instable ou si l'IP est bloquée. Essayez de redémarrer le service ou de supprimer le fichier de session pour recommencer.
*   **SyntaxError** : Corrigé (suppression des caractères invisibles).
