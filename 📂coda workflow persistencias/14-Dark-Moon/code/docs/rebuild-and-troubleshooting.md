# 🧹 Rebuild & Troubleshooting Darkmoon

Ce document explique :
- pourquoi un build peut échouer,
- quand rebuild,
- comment repartir proprement.

---

## 1. Erreurs Docker fréquentes (non bloquantes)

Exemple typique :

```bash
failed to solve: error getting credentials
````

Ou :

```bash
load metadata for docker.io/library/debian
````

👉 Ces erreurs :
- **ne viennent pas du projet**,
- sont liées au réseau Docker, WSL ou aux registries,
- sont **temporaires**.

### Solution simple

Relancer la commande :

```bash
docker compose build
````

ou :

```bash
docker compose up -d
```

---

## 2. Pourquoi Docker peut échouer

Causes fréquentes :

* timeout réseau,
* problème DNS,
* cache Docker corrompu,
* WSL instable (Windows).

👉 **Aucun lien avec la qualité du code ou des Dockerfiles.**

---

## 3. Script de rebuild propre : `recreate_clean.sh`

Darkmoon fournit un script dédié :

```bash
./recreate_clean.sh
```

### Ce que fait ce script

1. Stoppe la stack Docker
2. Supprime les bind mounts suivants :

   * `./data`
   * `./darkmoon-settings`
   * `$HOME/darkmoon-docker-fs`
3. Rebuild **sans cache**
4. Recrée la stack proprement

---

## 4. Pourquoi utiliser ce script

Ce script est **essentiel** si :

* vous avez modifié :

  * des agents,
  * `opencode.json`,
  * `auth.json`,
* vous avez des conflits de volumes,
* vous voulez un environnement propre,
* vous changez de modèle LLM.

👉 Il garantit :

* un état cohérent,
* une stack propre,
* aucune pollution des anciens builds.

---

## 5. Héritage intelligent de configuration

Même après un rebuild :

* les fichiers de configuration peuvent être **réinjectés**,
* les agents peuvent être **recopiés automatiquement**,
* la logique de seed ne s’exécute **qu’une seule fois**.

---

## 6. Quand NE PAS rebuild

Ne rebuild **pas** si :

* vous modifiez uniquement un agent Markdown,
* vous changez un prompt,
* vous modifiez un workflow Python dans un volume monté.

👉 Ces changements sont pris en compte **à chaud**.

---

## 7. Debug avancé

### Vérifier les conteneurs

```bash
docker ps
```

### Logs OpenCode

```bash
docker logs opencode
```

### Logs Darkmoon Toolbox

```bash
docker logs darkmoon
```

---

## 8. Résumé rapide

* Erreur Docker ≠ problème Darkmoon
* Relancer suffit souvent
* `recreate_clean.sh` = rebuild propre
* Volumes = modification sans rebuild

---

➡️ Pour comprendre l’architecture :
voir `docs/architecture.md`
