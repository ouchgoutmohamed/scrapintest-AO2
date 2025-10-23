# Contributing to PMMP Scraper

## 🤝 Comment contribuer

Nous accueillons les contributions ! Voici comment vous pouvez aider :

### Signaler un bug
1. Vérifiez que le bug n'a pas déjà été signalé
2. Créez une issue avec:
   - Description claire du problème
   - Étapes pour reproduire
   - Comportement attendu vs observé
   - Version de Python, OS, etc.
   - Logs pertinents

### Proposer une nouvelle fonctionnalité
1. Créez une issue pour discuter de la fonctionnalité
2. Attendez l'approbation avant de commencer le développement
3. Soumettez une Pull Request

### Soumettre une Pull Request

1. **Fork** le projet
2. **Créez une branche** pour votre fonctionnalité:
   ```bash
   git checkout -b feature/ma-fonctionnalite
   ```
3. **Commitez** vos changements:
   ```bash
   git commit -m "Ajout de ma fonctionnalité"
   ```
4. **Push** vers votre fork:
   ```bash
   git push origin feature/ma-fonctionnalite
   ```
5. **Ouvrez une Pull Request**

### Standards de code

- **PEP 8**: Suivre les conventions Python
- **Type hints**: Ajouter des annotations de type
- **Docstrings**: Documenter les fonctions et classes
- **Tests**: Ajouter des tests pour les nouvelles fonctionnalités
- **Commentaires**: Expliquer le "pourquoi", pas le "quoi"

### Tests

Avant de soumettre:
```bash
# Lancer les tests
pytest tests/ -v

# Vérifier le style
flake8 scraper/ api/ database/

# Vérifier les types (optionnel)
mypy scraper/ api/
```

### Domaines où contribuer

- 🐛 Correction de bugs
- 📝 Amélioration de la documentation
- ✨ Nouvelles fonctionnalités
- 🧪 Ajout de tests
- 🎨 Optimisation du code
- 🌍 Traductions
- 📊 Nouveaux dashboards Grafana

### Questions?

Ouvrez une issue avec le tag `question`

Merci de contribuer ! 🎉
