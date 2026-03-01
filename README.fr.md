<div align="center">

**🌐 [English](README.md) | [Francais](README.fr.md)**

<img src="assets/hero-banner.svg" alt="COUNCIL — Multi-Agent Reasoning Game" width="100%"/>

<br/>

**Chaque civilisation, chaque histoire, chaque conflit — reduisez-le a sa structure et vous trouvez toujours la meme chose : le bien contre le mal, un sauveur, un tueur, et la foule entre les deux.**
**COUNCIL est cette structure, vivante. Donnez-lui n'importe quel document et il fait emerger un reseau de personnages IA multi-agents qui s'observent, communiquent et conspirent entre eux — chacun portant des objectifs caches, des memoires evolutives et des loyautes mouvantes. Vous vous infiltrez parmi eux — et ils ne savent pas que vous etes humain.**

<br/>

[![Voir la demo](https://img.shields.io/badge/Voir_la_demo-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://youtu.be/RHimBYrIWE8)
[![Mistral AI](https://img.shields.io/badge/Powered_by-Mistral_AI-FA520F?style=for-the-badge&logo=mistralai&logoColor=white)](https://mistral.ai)
[![ElevenLabs](https://img.shields.io/badge/Voice_by-ElevenLabs-000000?style=for-the-badge&logo=elevenlabs&logoColor=white)](https://elevenlabs.io)

[![Python](https://img.shields.io/badge/Python_3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js_15-000000?logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![React](https://img.shields.io/badge/React_19-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![Three.js](https://img.shields.io/badge/Three.js-000000?logo=threedotjs&logoColor=white)](https://threejs.org)
[![Tailwind](https://img.shields.io/badge/Tailwind_CSS_4-06B6D4?logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![Supabase](https://img.shields.io/badge/Supabase-3FCF8E?logo=supabase&logoColor=white)](https://supabase.com)
[![Upstash](https://img.shields.io/badge/Upstash-00E9A3?logo=upstash&logoColor=white)](https://upstash.com)
[![Pydantic](https://img.shields.io/badge/Pydantic_v2-E92063?logo=pydantic&logoColor=white)](https://docs.pydantic.dev)
[![License MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![DeepWiki](https://img.shields.io/badge/DeepWiki-Explore_Codebase-2563EB?logo=bookstack&logoColor=white)](https://deepwiki.com/SunflowersLwtech/COUNCIL)

---

[Le jeu du test de Turing](#-le-jeu-du-test-de-turing) · [Fonctionnalites](#-fonctionnalites) · [Comment ca marche](#-comment-ca-marche) · [Pipeline de documents](#-pipeline-document-vers-jeu) · [Mistral AI](#-propulse-par-mistral-ai) · [ElevenLabs](#-propulse-par-elevenlabs) · [Moteur de tension](#-moteur-de-tension-dynamique) · [Streaming temps reel](#-streaming-en-temps-reel) · [Systeme multi-agents](#-systeme-multi-agents) · [Architecture des competences](#-architecture-modulaire-des-competences) · [Divulgation progressive](#-conception-par-divulgation-progressive) · [Architecture](#-architecture-du-systeme) · [Demarrage rapide](#-demarrage-rapide)

</div>

---

## Qu'est-ce que COUNCIL ?

COUNCIL est un moteur de jeu de deduction sociale alimente par l'IA qui transforme **n'importe quel document, histoire ou scenario** en une experience entierement jouable avec des personnages IA autonomes. Propulse par **Mistral AI** pour la cognition des personnages et **ElevenLabs** pour la synthese vocale, il cree 5 a 8 agents IA — chacun avec une personnalite unique, un role cache et un objectif evolutif — qui debattent, trompent, forment des alliances et s'eliminent mutuellement autour d'une table ronde virtuelle en 3D.

**Vous rejoignez en tant que joueur cache.** Les personnages IA ne savent pas si vous etes humain ou un agent. Pouvez-vous survivre au conseil ?

### L'innovation principale

La plupart des jeux IA vous donnent un chatbot avec qui parler. COUNCIL vous donne une **societe d'agents** avec des **objectifs caches concurrents** extraits de *votre propre contenu*.

> **Televersez un PDF** sur les intrigues de cour medievales → L'IA genere des Seigneurs, des Marchands et des Assassins, chacun avec un discours adapte a l'epoque, des loyautes cachees et des complots secrets.
>
> **Collez un extrait de science-fiction** → Les personnages deviennent des membres d'equipage d'une station spatiale traquant un saboteur — voix par ElevenLabs, animes en 3D, avec des souvenirs de ce que chaque autre personnage a dit.
>
> **Choisissez un scenario integre** → Plongez directement dans la deduction sociale classique avec des mondes pre-conçus.

---

## ✦ Le jeu du test de Turing

<div align="center">
<img src="assets/turing-test.svg" alt="The Turing Test Game — Hidden Human Among AI Agents" width="100%"/>
</div>

COUNCIL est le **test de Turing inverse en tant que gameplay**. Vous ne parlez pas a une IA — vous infiltrez une societe d'agents IA qui essaient de determiner si *vous* etes l'un d'entre eux.

| Dimension | Comment ca fonctionne |
|-----------|----------------------|
| **Identite cachee** | Un role et une faction secrets vous sont attribues. Les agents IA reçoivent le meme traitement. Personne ne sait qui est humain. |
| **Camouflage comportemental** | Pour survivre, vous devez imiter les schemas de parole, le raisonnement strategique et le comportement social des personnages IA. |
| **Pression sociale** | Les agents IA accusent, defendent et forment des alliances spontanement. Vos reponses sont jugees par rapport a leurs modeles mentaux du comportement « normal » d'un agent. |
| **Information asymetrique** | Vous voyez les pensees internes de l'IA via le ThinkingPanel — une fenetre sur leur raisonnement dont ils ignorent l'existence. |
| **Dynamiques emergentes** | Avec 5 a 8 agents independants + 1 humain cache, chaque session produit des dynamiques sociales, alliances et trahisons uniques. |

---

## ✦ Fonctionnalites

| Fonctionnalite | Description |
|----------------|-------------|
| **Moteur document-vers-jeu** | Televersez n'importe quel PDF ou texte. Mistral AI extrait le monde, les factions, les roles et les conditions de victoire automatiquement via OCR adaptative + extraction structuree. |
| **Personnages IA autonomes** | Chaque personnage possede une personnalite multicouche (Big Five, MBTI, traits Sims, Mind Mirror de Leary), un etat emotionnel, une memoire persistante et un suivi des relations qui evolue tout au long de la partie. |
| **Gameplay a roles caches** | Factions secretes (Bien contre Mal), actions nocturnes asymetriques (Tuer / Enqueter / Proteger / Empoisonner) et vote strategique avec raisonnement IA cache. |
| **Voix en temps reel** | ElevenLabs TTS donne a chaque personnage une voix unique avec une modulation emotionnelle. L'API Scribe permet la saisie vocale. L'attenuation audio intelligente melange la voix avec la musique d'ambiance adaptee a la phase. |
| **Table ronde 3D** | Scene Three.js immersive avec des avatars de personnages animes, une camera dynamique suivant le locuteur, des particules flottantes et un eclairage atmospherique. |
| **Mode Fantome** | Les joueurs elimines deviennent des spectateurs qui peuvent voir tous les roles caches et les pensees internes de l'IA — une fenetre sur le raisonnement reel des personnages IA. |
| **7 competences modulaires** | Modules cognitifs definis en YAML (Raisonnement strategique, Maitrise de la tromperie, Consolidation de la memoire, etc.) avec resolution de dependances, injection conditionnelle par faction et augmentation de prompt par priorite. |
| **Moteur de tension** | Suivi dynamique de la tension avec injection de complications narratives — revelations soudaines, pression temporelle, deplacements de soupçons et fissures d'alliances rendent chaque session imprevisible. |
| **Tout en streaming** | SSE diffuse 26 types d'evenements distincts — dialogues IA, votes, resultats nocturnes, complications — mot par mot vers le frontend en temps reel. Zero polling. |
| **Divulgation progressive** | Revelation strategique de l'information a travers les revelations d'elimination, le mode Fantome, les resultats nocturnes, le ThinkingPanel et les tableaux de statistiques de fin de partie. |

---

## ✦ Comment ca marche

<div align="center">
<img src="assets/game-flow.svg" alt="COUNCIL Game Flow" width="100%"/>
</div>

### Decomposition phase par phase

| Phase | Ce qui se passe | Mecanique cle |
|-------|----------------|---------------|
| **Telechargement** | Glissez-deposez un PDF, collez du texte ou selectionnez un scenario integre | Prend en charge les formats PDF, TXT, MD, DOC |
| **Generation** | Mistral AI extrait le modele du monde et cree 5 a 8 personnages (~60 s) | OCR adaptative + extraction JSON structuree |
| **Salon** | Consultez la liste des personnages, le cadre du monde et votre role secret | Revelation du role avec divulgation progressive |
| **Discussion** | Les personnages IA repondent en respectant leur personnage, reagissent spontanement, forment des alliances | 25 % de chance de reaction spontanee ; injection de complication en cas de stagnation |
| **Vote** | Votes IA paralleles via `asyncio.gather()` ; animation de revelation echelonnee | Egalite → decision du Maitre Agent via `make_ruling()` |
| **Revelation** | Le role cache du personnage elimine est expose a tous | Moment de divulgation progressive |
| **Nuit** | Tuer / Enqueter / Proteger / Empoisonner via l'appel de fonctions Mistral | Le Docteur sauve ; la Sorciere dispose de potions de sauvetage + poison |
| **Boucle** | Le cycle continue jusqu'a ce qu'une faction atteigne sa condition de victoire | Limite a 6 tours ; la faction majoritaire gagne |

---

## ✦ Pipeline document-vers-jeu

<div align="center">
<img src="assets/document-pipeline.svg" alt="Document-to-Game Pipeline" width="100%"/>
</div>

N'importe quel document devient un jeu vivant grace a un pipeline Mistral AI multi-etapes :

```
PDF / Texte / Histoire
       │
       ▼
  mistral-ocr-latest ──── Traitement adaptatif de documents
  ─────────────────────   • Petits docs (<50K car.) : OCR directe
                          • Grands docs (>120K car.) : hierarchique
                            decoupage → resume → combinaison
       │
       ▼
  mistral-large-latest ──► WorldModel (valide par Pydantic v2)
  ─────────────────────    • Cadre, epoque, atmosphere
  Extraction JSON          • Factions avec alignements
  structuree               • Roles et conditions de victoire
                           • Enjeux narratifs et conflits
       │
       ▼
  Character Factory ──────► 5 a 8 personnages uniques
  mistral-large-latest      Chacun genere avec :
  ─────────────────────     • Personnage public + role secret
  Synthese de personnalite  • Big Five + MBTI + traits Sims (budget 25 pts)
  multidimensionnelle       • Mind Mirror (4 plans de pensee Leary)
  + 3 tentatives            • Regles comportementales + style de parole unique
       │
       ▼
  Session de jeu ──────────── Roles attribues · Competences injectees · Scene 3D chargee
```

---

## ✦ Propulse par Mistral AI

Mistral AI est l'**epine dorsale cognitive** de COUNCIL. Chaque pensee de personnage, decision strategique et battement narratif est pilote par la suite de modeles de Mistral.

<div align="center">
<img src="assets/mistral-integration.svg" alt="Mistral AI Integration" width="100%"/>
</div>

### Carte d'utilisation des modeles

| Tache | Modele | Technique | Pourquoi ce modele |
|-------|--------|-----------|-------------------|
| OCR de documents | `mistral-ocr-latest` | Dimensionnement adaptatif : directe (<50K) ou hierarchique decoupage→resume→combinaison | Meilleur OCR de sa categorie pour PDF/texte mixte |
| Extraction du monde | `mistral-large-latest` | Mode JSON + validation Pydantic v2 | Raisonnement structure complexe sur des recits arbitraires |
| Generation de personnages | `mistral-large-latest` | Schema JSON multi-champs ; 3 tentatives + backoff exponentiel | Synthese coherente de personnalite multidimensionnelle |
| Dialogue en personnage | `mistral-large-latest` | Streaming SSE ; prompt systeme 4 couches avec injections de competences | Qualite narrative + fidelite au personnage |
| Vote strategique | `mistral-large-latest` | **Appel de fonctions** : `cast_vote(target_id, reasoning)` | Sortie structuree avec raisonnement cache |
| Actions nocturnes | `mistral-large-latest` | **Appel de fonctions** : `night_action(action_type, target_id, reasoning)` | Decisions structurees adaptees au role |
| Narration | `mistral-large-latest` | 12 modeles narratifs + injection de complications | Generation creative avec conscience de la phase |
| Selection des repondants | `mistral-small-latest` | JSON : quels personnages doivent repondre | Filtrage a faible latence avant generation |
| Ordre de parole | `mistral-small-latest` | JSON : ordre dynamique des personnages par tour | Coordination economique |
| Analyse emotionnelle | `mistral-small-latest` | JSON : mise a jour de l'etat emotionnel sur 6 axes | Mises a jour frequentes, modele rapide et economique |
| Resumes de tours | `mistral-small-latest` | Compression de discussion pour la memoire des agents | Memoire a long terme economique |
| Departage | `mistral-large-latest` | « Maitre Agent » avec contexte complet → re-vote / passer / personnalise | Les decisions a forts enjeux necessitent le modele le plus capable |

### L'architecture de prompt a 4 couches pour les personnages

Chaque personnage IA est construit comme un prompt systeme en couches — un modele psychologique qui separe ce que le personnage *montre* de ce qu'il *sait* et *veut* :

```
╔═══════════════════════════════════════════════════════════════╗
║  COUCHE 1 — CERVEAU STRATEGIQUE (cache de tous les agents)    ║
║  Role cache · Faction · Condition de victoire · Regles        ║
║  comportementales                                             ║
║  « Ne jamais reveler votre role. Detourner les soupçons. »    ║
╠═══════════════════════════════════════════════════════════════╣
║  COUCHE 2 — COEUR DU PERSONNAGE (personnage public)           ║
║  Nom · Style de parole · Role public                          ║
║  Desir : « Obtenir le pouvoir politique »                     ║
║  Methode : « Par la manipulation »                            ║
║  Valeurs morales · Style de decision · Secret profond         ║
╠═══════════════════════════════════════════════════════════════╣
║  COUCHE 3 — ADN DE PERSONNALITE                               ║
║  Big Five (O/C/E/A/N) · Type MBTI                             ║
║  Traits Sims : ordre/sociabilite/activite/jeu/gentillesse     ║
║  (budget 25 pts)                                              ║
║  Mind Mirror (4 plans de Leary) : bio · emotionnel · mental · ║
║  social → Chaque plan genere un « jazz » comportemental unique║
╠═══════════════════════════════════════════════════════════════╣
║  COUCHE 4 — ETAT DYNAMIQUE + INJECTIONS DE COMPETENCES        ║
║  Etat emotionnel : bonheur·colere·peur·confiance·energie·    ║
║  curiosite                                                    ║
║  Memoire : MCT (10 evenements) · Episodique (8 resumes) ·    ║
║  Semantique                                                   ║
║  Relations : proximite par personnage (0-1) + confiance (-1,1)║
║  + 7 injections de competences YAML (filtrees par faction,    ║
║  triees par priorite)                                         ║
╚═══════════════════════════════════════════════════════════════╝
```

### Appel de fonctions Mistral en action

COUNCIL utilise l'**API d'appel de fonctions** de Mistral pour les decisions structurees les plus critiques du jeu :

```python
GAME_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "cast_vote",
            "description": "Vote to eliminate a player from the council",
            "parameters": {
                "properties": {
                    "target_id": {"type": "string"},
                    "reasoning": {"type": "string",
                                  "description": "Internal reasoning (hidden from others)"},
                },
                "required": ["target_id", "reasoning"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "night_action",
            "parameters": {
                "properties": {
                    "action_type": {
                        "type": "string",
                        "enum": ["kill", "investigate", "protect", "save", "poison", "none"]
                    },
                    "target_id": {"type": "string"},
                    "reasoning": {"type": "string"}
                }
            }
        }
    }
]
```

### Defense anti-jailbreak

Les personnages sont renforces contre l'injection de prompts, la derive de personnalite et l'auto-divulgation IA :

- **Regles comportementales** appliquees a la couche 1 du prompt systeme
- **Filtrage par motifs** : detection regex de phrases typiques de l'IA (« As an AI », « language model », etc.)
- **Suivi des faits canoniques** : les personnages ne contredisent jamais leur propre historique declare
- **`_validate_in_character()`** validation de la reponse a chaque generation
- **Suppression des phrases IA** appliquee a toutes les sorties avant livraison

### Moteur de tension et de complications

Le Maitre du Jeu surveille un score de tension continu et injecte des complications narratives (Revelation, Pression temporelle, Deplacement de soupçons, Fissure d'alliance, Preuve) lorsque la discussion stagne ou qu'un consensus se forme trop rapidement. Voir **[Moteur de tension dynamique](#-moteur-de-tension-dynamique)** pour la description complete.

---

## ✦ Propulse par ElevenLabs

ElevenLabs transforme COUNCIL d'un jeu textuel en une **experience cinematographique**. Les personnages ne se contentent pas de repondre — ils parlent avec des voix distinctes porteuses d'emotion, d'accent et de personnalite.

<div align="center">
<img src="assets/voice-pipeline.svg" alt="ElevenLabs Voice Pipeline" width="100%"/>
</div>

### Architecture vocale

| Fonctionnalite | Implementation | Details |
|----------------|---------------|---------|
| **Synthese vocale** | ElevenLabs TTS (eleven_v3) | Chaque personnage est associe a une voix unique parmi un pool de 8 voix. Streaming en temps reel par audio fragmente. |
| **Balises d'emotion** | Injection automatique | Etat emotionnel sur 6 axes → balises ElevenLabs v3 : `[angry]`, `[scared]`, `[excited]`, `[suspicious]`, `[curious]`, `[sighs]` |
| **Reconnaissance vocale** | ElevenLabs Scribe v2 | Transcription en temps reel via WebSocket. Jetons a usage unique. Affichage de transcription partielle. Repli sur l'API Web Speech du navigateur. |
| **File d'attente vocale** | Systeme personnalise | Lecture sequentielle multi-agents. Repli par Blob pour l'instabilite reseau. |
| **Attenuation audio** | Evenements personnalises | La musique de fond passe de 0.25→0.08 lorsque les personnages parlent. Volumes adaptes a la phase : nuit (0.15), discussion (0.25), vote (0.35). |

### Pourquoi les balises d'emotion sont importantes

Chaque reponse de personnage est analysee par un modele emotionnel a 6 dimensions *avant* la synthese vocale :

- Un personnage avec `fear: 0.8` apres une accusation → voix `[scared]`
- Un Loup-Garou se defendant avec `trust: 0.2` → tonalite `[suspicious]`
- Un Docteur qui a sauve quelqu'un pendant la nuit → `[excited]` le lendemain matin

La voix *correspond* a l'etat emotionnel interne du personnage — aucun appel LLM supplementaire necessaire.

---

## ✦ Moteur de tension dynamique

<div align="center">
<img src="assets/tension-engine.svg" alt="Dynamic Tension Engine — Adaptive Narrative Complication System" width="100%"/>
</div>

COUNCIL ne s'appuie pas sur des battements narratifs scriptes. Le **Moteur de tension** suit en continu la temperature emotionnelle du jeu et injecte dynamiquement des complications narratives lorsque la discussion stagne, qu'un consensus se forme trop rapidement ou qu'une faction avance sans opposition.

### Comment la tension est calculee

```
tension = f(elimination_ratio, round_progression, recent_kills, vote_splits, silence_duration)
```

| Signal d'entree | Ce qu'il mesure | Effet sur la tension |
|-----------------|----------------|---------------------|
| **Ratio d'elimination** | Combien de joueurs ont ete elimines | Ratio plus eleve → tension de base plus elevee |
| **Progression des tours** | Quel tour le jeu a atteint (T1–T6) | Tours avances → urgence croissante |
| **Eliminations recentes** | Eliminations nocturnes dans les 1-2 derniers tours | Les eliminations font monter brusquement la tension |
| **Partage des votes** | A quel point le dernier vote etait serre | Votes serres → suspicion croissante |
| **Duree du silence** | Temps ecoule depuis le dernier echange significatif | Long silence → declenche une complication |

### 5 types de complications

Lorsque la tension depasse un seuil — ou lorsque la discussion stagne — le Maitre du Jeu injecte l'une des cinq complications narratives :

| Complication | Declencheur | Effet en jeu |
|-------------|------------|--------------|
| **Revelation** | Des informations cachees emergent | « L'histoire de quelqu'un ne colle pas — un detail contredit ce qui a ete dit il y a deux tours. » |
| **Pression temporelle** | Escalade de l'urgence | « Le conseil exige une action decisive MAINTENANT. Plus de deliberation. » |
| **Deplacement de soupçons** | Redirection de la culpabilite | « Les regards se tournent vers quelqu'un qui est reste suspicieusement silencieux lors de chaque accusation. » |
| **Fissure d'alliance** | Fractures de confiance | « Deux allies echangent un regard tendu — quelque chose de non-dit plane entre eux. » |
| **Preuve** | De nouveaux indices emergent | « Un element de preuve est decouvert qui change tout par rapport au vote precedent. » |

Les complications sont **non repetitives au sein d'une session** et s'intensifient au fil des tours. Le resultat : chaque partie suit un arc de tension croissant, avec des points de pression strategiques qui forcent de veritables prises de decision.

---

## ✦ Streaming en temps reel

<div align="center">
<img src="assets/realtime-streaming.svg" alt="Real-Time SSE Streaming — 26 Event Types, Zero Polling" width="100%"/>
</div>

COUNCIL utilise les **Server-Sent Events (SSE)** pour delivrer chaque interaction de jeu en temps reel — dialogues mot par mot, revelations de vote une par une, et resultats nocturnes action par action. Zero polling. Zero delai requete-reponse.

### 26 types d'evenements repartis en 4 categories

| Categorie | Evenements | Objectif |
|-----------|-----------|---------|
| **Dialogue** (8) | `thinking`, `ai_thinking`, `responders`, `stream_start`, `stream_delta`, `stream_end`, `response`, `reaction` | Parole des personnages IA mot par mot avec indicateurs de reflexion |
| **Vote** (5) | `voting_started`, `vote`, `tally`, `elimination`, `player_eliminated` | Revelations de votes echelonnees avec rythme dramatique |
| **Nuit** (5) | `night_started`, `night_action`, `night_results`, `night_kill_reveal`, `investigation_result` | Actions secretes resolues avec revelations cinematographiques |
| **Systeme** (8) | `complication`, `narration`, `discussion_warning`, `discussion_ending`, `game_over`, `last_words`, `error`, `done` | Controle du flux de jeu et injection narrative |

### Architecture

```
Backend (FastAPI)                    Frontend (Next.js)
─────────────────                    ──────────────────
Orchestrator                         SSE Consumer
  │ asyncio.gather()                   │ fetch + ReadableStream
  │ parallel agent calls               │ reader.read() loop
  ▼                                    ▼
SSE Emitter ──── data: {...}\n\n ───► GameStateProvider
  │ StreamingResponse                    │ React Context
  │ yield f"data: {json}\n\n"           │ dispatch by event type
  ▼                                    ▼
Game Master                          UI Components
  │ narration + tension                │ ChatDrawer (mot par mot)
  │ complication injection             │ VotePanel (revelation echelonnee)
  ▼                                    │ NightActionPanel
AI Agents                             │ RoundtableScene (3D)
  │ Mistral streaming                  ▼
  │ function calling                 Connecte · 0ms polling
```

Chaque reponse de personnage est diffusee sous forme d'evenements `stream_delta` — le frontend accumule les tokens et les affiche caractere par caractere. Les revelations de votes utilisent des evenements `vote` avec des delais echelonnes pour la tension dramatique. Les resultats nocturnes arrivent en sequence pour creer le suspense : `night_started` → `night_action` → `night_results` → `night_kill_reveal`.

---

## ✦ Systeme multi-agents

<div align="center">
<img src="assets/multi-agent.svg" alt="Multi-Agent Character System" width="100%"/>
</div>

### Ce qui en fait un veritable systeme multi-agents

Contrairement au jeu de role avec chatbot ou aux jeux a PNJ unique, COUNCIL implemente une veritable architecture multi-agents :

| Propriete | Implementation |
|-----------|---------------|
| **Raisonnement independant** | Chaque agent possede son propre prompt systeme, ses informations cachees et son historique de conversation |
| **Memoire persistante** | Memoire a 3 niveaux : MCT (10 evenements), Episodique (8 resumes de tours), Semantique (faits canoniques) |
| **Suivi des relations** | `closeness` (0–1) et `trust` (-1 a 1) par personnage, mis a jour apres chaque interaction |
| **Evolution emotionnelle** | Emotions sur 6 axes (bonheur, colere, peur, confiance, energie, curiosite) mises a jour via LLM + repli par mots-cles ; decroissance vers le neutre a chaque tour |
| **Reactions spontanees** | 25 % de probabilite par message de reponse non sollicitee de PNJ — dynamiques de groupe organiques |
| **Confidentialite strategique** | La justification cachee des votes et le raisonnement des actions nocturnes ne sont jamais partages avec les autres agents |
| **Ordre de parole dynamique** | Determine par l'IA a chaque tour via `mistral-small-latest` — pas d'ordre de tour fixe |

### Le systeme d'etat emotionnel

Les emotions parcourent l'ensemble du pipeline :

```
Analyse LLM (mistral-small) + Detection par mots-cles
           ↓
   Etat emotionnel sur 6 axes
   bonheur · colere · peur · confiance · energie · curiosite
           ↓
    ┌──────┴──────────┬────────────────┬──────────────┐
    ↓                 ↓                ↓              ↓
  Prompt systeme    ElevenLabs      Liste des      Indicateurs
  (module par la    Balises         personnages    emoji UI
   personnalite)    d'emotion       Affichage      😠😟😊🤨🤔
                    [angry]
                    [scared]
                    [excited]
```

---

## ✦ Architecture modulaire des competences

<div align="center">
<img src="assets/skills-system.svg" alt="Modular Skills Architecture" width="100%"/>
</div>

COUNCIL implemente un **systeme de competences cognitives modulaire** — 7 modules de competences definis en YAML qui augmentent l'intelligence des agents a l'execution via une injection de prompts resolue par dependances et conditionnee par faction.

### Pourquoi les competences sont importantes

Les competences ne sont pas des prompts statiques. Ce sont des **modules cognitifs composables** qui :

- **Resolvent les dependances** — La Maitrise de la tromperie integre automatiquement le Raisonnement strategique
- **Detectent les conflits** — Les competences incompatibles declenchent des erreurs avant le debut du jeu
- **Filtrent par faction** — Les agents du Mal reçoivent des *instructions fondamentalement differentes* de celles des agents du Bien pour le meme module de competence
- **Ciblent des contextes specifiques** — Les competences s'injectent exactement dans le bon prompt (vote, actions nocturnes, narration, etc.)
- **Trient par priorite** — Les numeros de priorite plus bas s'injectent en premier, construisant le raisonnement fondamental avant les techniques avancees
- **Mettent en cache paresseusement** — Par tuple `(skill, target, faction)`, calcule une fois et reutilise

### Les 7 modules cognitifs

| # | Competence | Priorite | Cibles | Ce qu'elle apporte |
|---|-----------|----------|--------|-------------------|
| 1 | **Strategic Reasoning** | 10 | character_agent, vote_prompt, night_action | **Pipeline SSRSR en 5 etapes** : Situation → Carte des soupçons → Reflexion → Strategie → Reponse. Les agents executent interieurement une cognition structuree de pre-reponse avant chaque replique. |
| 2 | **Contrastive Examples** | 15 | character_agent, vote_prompt | Exemples comportementaux bons/mauvais via l'apprentissage en contexte. Montre aux agents a quoi ressemble un jeu *excellent* versus *mediocre* avec des exemples concrets avant/apres. |
| 3 | **Memory Consolidation** | 20 | character_agent, round_summary | **Systeme de memoire a 3 niveaux** : MCT (10 evenements bruts), Episodique (8 resumes de tours compresses), Semantique (faits canoniques jamais contredits). Reconnaissance de motifs inter-tours. |
| 4 | **Goal-Driven Behavior** | 25 | character_agent, night_action | **Couplage emotion-objectif** : La peur conduit a la survie, la curiosite conduit a l'enquete, la colere conduit a la justice, l'energie conduit a l'influence. L'etat emotionnel determine quel sous-objectif domine. |
| 5 | **Deception Mastery** | 30 | character_agent, vote_prompt | **Injection scindee par faction** : Les agents du Mal apprennent la deflection, la construction d'alibis, le sacrifice d'allies, le partage controle d'informations. Les agents du Bien apprennent la verification de coherence, l'analyse des schemas de vote, les tests de pression, l'analyse du silence. |
| 6 | **Discussion Dynamics** | 40 | character_agent, spontaneous_reaction | Conscience de la prise de parole, regles anti-repetition, adaptation de l'energie, directives de reponse ciblee. Les reactions spontanees ne se declenchent que sur les contradictions, accusations ou surprises reelles. |
| 7 | **Social Evaluation** | 60 | narration | Conscience des dynamiques sociales pour le Maitre du Jeu : changements d'influence, erosion de la confiance, formation d'alliances, detection de l'isolement, indices de tension tisses dans la narration atmospherique. |

### Plongee dans l'architecture des competences

```
backend/game/skills/
├── strategic_reasoning/      priority: 10
│   ├── SKILL.md              Frontmatter: id, name, targets, priority, behavioral_rules
│   └── injections/
│       ├── character_agent.md    ← Universel : pipeline SSRSR en 5 etapes
│       ├── vote_prompt.md        ← Universel : vote base sur les preuves
│       └── night_action.md       ← Universel : ciblage strategique
│
├── deception_mastery/        priority: 30  │  depends_on: [strategic_reasoning]
│   ├── SKILL.md
│   └── injections/
│       ├── character_agent_evil.md   ← Mal : deflection, alibi, sacrifice d'allies
│       ├── character_agent_good.md   ← Bien : coherence, schemas de vote, pression
│       ├── vote_prompt_evil.md       ← Mal : strategie de preservation de couverture
│       └── vote_prompt_good.md       ← Bien : detection d'incoherences
│
└── ... (5 autres competences avec la meme structure)
```

### Le pipeline SkillLoader

```
┌──────────────┐    ┌────────────────┐    ┌────────────────┐
│ Decouverte    │    │ Resolution      │    │ Detection       │
│ YAML          │ →  │ des dependances │ →  │ des conflits    │
│ Scan skills/  │    │ DFS recursif    │    │ Verification    │
│ Parse SKILL.md│    │ avec detection  │    │ croisee de      │
│ par repertoire│    │ de cycles       │    │ toutes les      │
└──────────────┘    └────────────────┘    │ paires resolues │
        ↓                                 └────────────────┘
┌──────────────┐    ┌────────────────┐           ↓
│ Tri par       │    │ Filtrage par    │    ┌────────────────┐
│ priorite      │ →  │ faction         │ →  │ Injection       │
│ Numero plus   │    │ evil_factions   │    │ de prompt       │
│ bas = injecte │    │ → _evil.md ou   │    │ Cache par       │
│ en premier    │    │   _good.md      │    │ (skill, target, │
└──────────────┘    └────────────────┘    │  faction) tuple │
                                           └────────────────┘
```

### Injection conditionnelle par faction — L'innovation cle

Le meme module de competence produit un **comportement d'agent fondamentalement different** selon la faction :

<table>
<tr>
<th>🔴 Agent du Mal (Deception Mastery)</th>
<th>🔵 Agent du Bien (Deception Mastery)</th>
</tr>
<tr>
<td>

**Deflection** : Lorsqu'il est accuse, rediriger les soupçons avec des preuves specifiques contre quelqu'un d'autre

**Construction d'alibi** : Voter avec la majorite tot pour accumuler du capital de confiance en vue d'une trahison ulterieure

**Sacrifice d'allies** : Si un allie du Mal est sur le point d'etre expose, rejoindre l'accusation pour maintenir sa couverture

**Information controlee** : Partager juste assez pour sembler utile sans reveler quoi que ce soit de reel

</td>
<td>

**Verification de coherence** : Suivre les affirmations a travers les tours — les menteurs se contredisent au fil du temps

**Analyse des schemas de vote** : Les joueurs du Mal votent ensemble — chercher les blocs qui se protegent mutuellement

**Tests de pression** : Questions directes + observer les reactions — l'explication excessive et la deflection sont des indices

**Analyse du silence** : Les joueurs silencieux lors de moments critiques peuvent eviter le risque

</td>
</tr>
</table>

### Comment les competences s'injectent dans le systeme de prompts

Les competences se connectent a l'architecture `CHARACTER_SYSTEM_PROMPT` a 5 niveaux :

```
Niveau 1 : REGLES ABSOLUES         ← Garde-fous anti-jailbreak
Niveau 2 : CERVEAU STRATEGIQUE     ← Role cache, faction, condition de victoire
                                      + behavioral_rules des competences fusionnees ici
Niveau 3 : COEUR DU PERSONNAGE     ← Personnage public, style de parole
Niveau 4 : ADN DE PERSONNALITE     ← Big Five, MBTI, Sims, Mind Mirror
Niveau 5 : ETAT DYNAMIQUE          ← Emotions, memoire, relations
                                      + injections character_agent des competences ici
         COMPORTEMENT HUMAIN       ← Traduction traits-vers-comportement
```

La cible `character_agent` est la seule integree dans le prompt systeme statique. Toutes les autres cibles (`vote_prompt`, `night_action`, `round_summary`, `spontaneous_reaction`, `narration`) sont ajoutees dynamiquement au prompt du tour de l'utilisateur au moment de chaque action de jeu specifique.

### 7 cibles d'injection

| Cible | Quand elle se declenche | Utilisee par |
|-------|------------------------|-------------|
| `character_agent` | Chaque reponse (prompt systeme statique) | Strategic Reasoning, Contrastive Examples, Memory Consolidation, Goal-Driven, Deception Mastery, Discussion Dynamics |
| `vote_prompt` | Decisions de vote | Strategic Reasoning, Contrastive Examples, Deception Mastery |
| `night_action` | Actions secretes de la phase nocturne | Strategic Reasoning, Goal-Driven |
| `round_summary` | Compression memoire de fin de tour | Memory Consolidation |
| `spontaneous_reaction` | Interjections non sollicitees de PNJ | Discussion Dynamics |
| `narration` | Texte d'ambiance du Maitre du Jeu | Social Evaluation |
| `responder_selection` | Reserve pour de futures competences | — |

---

## ✦ Conception par divulgation progressive

<div align="center">
<img src="assets/progressive-disclosure.svg" alt="Progressive Disclosure Design" width="100%"/>
</div>

COUNCIL separe l'**information publique** de l'**information cachee** a chaque couche, creant un suspense naturel et une profondeur strategique grace a des revelations soigneusement minutees.

### Couches d'information

| PUBLIC (visible par tous) | CACHE (revele progressivement) |
|--------------------------|-------------------------------|
| Nom et avatar du personnage | Role cache (Loup-Garou / Voyant / Docteur / Sorciere) |
| Style de parole et role public | Alignement de faction (Bien contre Mal) |
| Comportement observable et declarations | Condition de victoire |
| Reputation relationnelle | Raisonnement interne des votes |
| Indicateurs emotionnels | Justification des actions nocturnes |
| | Monologue interieur de l'IA |

### 5 moments de revelation

| # | Moment | Ce qui est revele | Qui le voit |
|---|--------|------------------|-------------|
| 1 | **Elimination** | Profil cache complet du personnage elimine — role, faction, regles comportementales | Tous les joueurs |
| 2 | **Mode Fantome** | TOUS les roles caches + pensees internes de l'IA pour chaque personnage | Joueur elimine uniquement |
| 3 | **Resultats nocturnes** | Resultats des actions tuer/sauver/proteger ; resultat d'enquete | Tous voient les resultats ; le Voyant voit l'enquete en prive |
| 4 | **Fin de partie** | Tableau de scores complet — role de chaque personnage, chronologie des evenements cles, tours survecu | Tous les joueurs |
| 5 | **ThinkingPanel** | Monologue interieur du personnage IA *avant* qu'il ne parle publiquement | Joueur humain uniquement (interface de meta-transparence) |

---

## ✦ Architecture du systeme

<div align="center">
<img src="assets/architecture.svg" alt="COUNCIL System Architecture" width="100%"/>
</div>

### Vue d'ensemble de la pile technique

| Couche | Technologie | Role |
|--------|------------|------|
| **Frontend** | Next.js 15 · React 19 · TypeScript | Shell applicatif, routage, etat du jeu via React Context |
| **Scene 3D** | Three.js ~0.175 · React Three Fiber · @react-three/drei | Scene de table ronde, figures d'agents animees, camera dynamique |
| **Style** | Tailwind CSS 4 | Interface responsive avec design sombre thematise par phase |
| **Backend** | Python 3.12 · FastAPI | API REST + streaming SSE, orchestration de jeu asynchrone |
| **Moteur LLM** | Mistral AI SDK | Toute la cognition des personnages, generation de monde, vote, narration |
| **Voix** | ElevenLabs SDK (eleven_v3 / scribe_v2) | TTS avec balises d'emotion, STT en temps reel |
| **Etat de session** | Redis via Upstash (TTL 24 h) | Etat de jeu actif + memoires des agents, ecritures atomiques par pipeline |
| **Base analytique** | Supabase (PostgreSQL) | Stockage de sessions long terme, synchronisation asynchrone fire-and-forget |
| **Validation** | Pydantic v2 | Analyse de toutes les reponses LLM avec validateurs personnalises + tentatives |

### Architecture de streaming SSE

Toutes les interactions de jeu utilisent les Server-Sent Events avec **26 types d'evenements distincts** repartis en 4 categories — zero polling, livraison mot par mot. Voir **[Streaming en temps reel](#-streaming-en-temps-reel)** pour le catalogue complet des evenements et le diagramme d'architecture.

### Persistance a double couche

```
Action de jeu
    │
    ▼
Redis (Upstash) — COUCHE CHAUDE
────────────────────────────────
• Pipeline atomique : etat + toutes les memoires des agents en une transaction
• TTL de 24 heures par session
• Relecture immediate pour la recuperation de session
    │
    ▼ (fire-and-forget via asyncio.ensure_future)
Supabase (PostgreSQL) — COUCHE FROIDE
───────────────────────────────────
• Upsert de la table game_sessions
• Analytique long terme
• Ne bloque pas la reponse du jeu
```

### Ingenierie de la scene 3D

La scene Three.js de la table ronde utilise une gestion prudente des ressources GPU :

- **Pas de React Strict Mode** — empeche l'epuisement des ressources GPU par double montage
- **Pas de PostProcessing** — elimine les framebuffers de l'EffectComposer
- **Pas d'ombres** — supprime les allocations de shadow map
- **Pas d'environnement HDRI** — elimine la charge GPU des textures cubemap
- **three.js fixe a ~0.175.0** — compatibilite avec la bibliotheque postprocessing

L'atmosphere visuelle est obtenue via `FloatingParticles` (100 lucioles, melange additif), `SciFiFloor` (reflectif + anneaux de grille concentriques), materiaux emissifs oscillants sur les figures d'agents, et 1500 particules `Stars`.

---

## ✦ Demarrage rapide

### Prerequis

- [Conda](https://docs.conda.io/en/latest/) (Miniconda ou Anaconda)
- [Node.js](https://nodejs.org/) 18+
- [Cle API Mistral AI](https://console.mistral.ai/) — requise
- [Cle API ElevenLabs](https://elevenlabs.io/) — optionnelle (fonctionnalites vocales)

### 1. Cloner et configurer

```bash
git clone https://github.com/your-username/COUNCIL.git
cd COUNCIL

conda create -n council python=3.12 -y
conda activate council
```

### 2. Installer les dependances

```bash
# Backend
pip install -r requirements.txt

# Frontend
cd frontend && npm install && cd ..
```

### 3. Configurer les cles API

```bash
cp .env.example .env
```

Editez `.env` :

```env
# Required
MISTRAL_API_KEY=your_mistral_api_key

# Voice (optional — text-only without these)
ELEVENLABS_API_KEY=your_elevenlabs_api_key

# Persistence (optional — in-memory only without these)
UPSTASH_REDIS_URL=your_upstash_redis_url
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
```

### 4. Lancer

```bash
# Terminal 1 — Backend (FastAPI sur :8000)
conda activate council
python run.py

# Terminal 2 — Frontend (Next.js sur :3000)
cd frontend
npm run dev
```

Ouvrez **[http://localhost:3000](http://localhost:3000)** et commencez a jouer.

---

## ✦ Reference API

Toutes les interactions de jeu sont diffusees via SSE. Les reponses arrivent mot par mot, vote par vote, action par action.

| Point d'acces | Methode | Description |
|---------------|---------|-------------|
| `/api/game/create` | POST | Creer une partie a partir d'un fichier televerse ou d'un texte colle |
| `/api/game/scenario/{id}` | POST | Creer une partie a partir d'un scenario integre |
| `/api/game/{id}/start` | POST | Transition salon → discussion ; attribuer le role du joueur |
| `/api/game/{id}/chat` | POST | Envoyer un message → flux SSE de reponses des personnages IA |
| `/api/game/{id}/open-discussion` | POST | Declencher un tour de discussion IA non sollicite |
| `/api/game/{id}/vote` | POST | Voter → flux SSE de revelations de votes echelonnees |
| `/api/game/{id}/night` | POST | Declencher la phase nocturne → flux SSE d'actions nocturnes |
| `/api/game/{id}/night-chat` | POST | Communication nocturne du joueur (fantome/specifique au role) |
| `/api/game/{id}/night-action` | POST | Soumettre l'action nocturne secrete du joueur |
| `/api/game/{id}/state` | GET | Etat complet du jeu (`?full=true` pour les donnees completes) |
| `/api/game/{id}/player-role` | GET | Obtenir l'attribution du role cache du joueur |
| `/api/game/{id}/reveal/{char}` | GET | Obtenir le profil cache complet du personnage elimine |
| `/api/voice/tts` | POST | Generer l'audio TTS du personnage |
| `/api/voice/tts/stream` | GET | Diffuser l'audio TTS par fragments pour une lecture en temps reel |
| `/api/voice/scribe-token` | POST | Generer un jeton de session STT a usage unique |
| `/api/voice/sfx` | POST | Generer un effet sonore via ElevenLabs |
| `/api/skills` | GET | Lister les modules de competences cognitives disponibles |
| `/api/game/scenarios` | GET | Lister les scenarios de jeu integres |

---

## ✦ Structure du projet

```
COUNCIL/
├── backend/
│   ├── server.py                     # Application FastAPI — toutes les routes API
│   ├── game/
│   │   ├── orchestrator.py           # Gestion de session, coordination des phases, SSE
│   │   ├── game_master.py            # Narration, tension, vote, complications
│   │   ├── character_agent.py        # Systeme de prompt a 4 couches, moteur IA emotionnel
│   │   ├── character_factory.py      # Generation de personnages LLM (Sims + Mind Mirror)
│   │   ├── document_engine.py        # OCR → WorldModel pipeline adaptatif
│   │   ├── skill_loader.py           # Decouverte YAML, resolution de dependances, injection
│   │   ├── persistence.py            # Redis (chaud) + Supabase (froid) double couche
│   │   ├── state.py                  # Machine a etats des phases + serialisation
│   │   ├── prompts.py                # Tous les modeles de prompts (14 systemes de prompts)
│   │   ├── adversarial_tester.py     # Suite de tests de robustesse (14 sondes jailbreak)
│   │   └── skills/                   # 7 modules de competences cognitives YAML
│   │       ├── strategic_reasoning/  # Pipeline SSRSR en 5 etapes (P:10)
│   │       ├── contrastive_examples/ # Exemples comportementaux bons/mauvais (P:15)
│   │       ├── memory_consolidation/ # Systeme de memoire a 3 niveaux (P:20)
│   │       ├── goal_driven_behavior/ # Couplage emotion-objectif (P:25)
│   │       ├── deception_mastery/    # Tromperie/detection scindee par faction (P:30)
│   │       ├── discussion_dynamics/  # Prise de parole, anti-repetition (P:40)
│   │       └── social_evaluation/    # Dynamiques sociales pour la narration (P:60)
│   ├── agents/
│   │   └── base_agent.py             # Classe de base asynchrone Mistral
│   ├── models/
│   │   └── game_models.py            # Modeles de donnees Pydantic v2 (20+ modeles)
│   └── voice/
│       └── tts_middleware.py          # ElevenLabs TTS/STT + injection de balises d'emotion
│
├── frontend/
│   ├── app/                          # Next.js App Router
│   │   ├── layout.tsx                # Layout racine, meta PWA, i18n
│   │   └── page.tsx                  # GameRouter + GameEndScreen
│   ├── components/
│   │   ├── GameBoard.tsx             # Interface de jeu principale + overlays
│   │   ├── VotePanel.tsx             # Animation de revelation de votes echelonnee
│   │   ├── NightActionPanel.tsx      # Interface d'action nocturne specifique au role
│   │   ├── GhostOverlay.tsx          # Vue spectateur avec roles caches
│   │   ├── ThinkingPanel.tsx         # Affichage des pensees internes de l'IA
│   │   ├── DocumentUpload.tsx        # Glisser-deposer + texte + selection de scenario
│   │   ├── GameLobby.tsx             # Liste des personnages + revelation du role
│   │   └── scene/                    # Composants Three.js de la table ronde 3D
│   │       ├── RoundtableScene.tsx   # Config Canvas + frontiere d'erreur
│   │       ├── RoundtableCanvas.tsx  # Particules, sol, etoiles
│   │       ├── AgentFigure.tsx       # Personnages 3D animes
│   │       ├── CameraRig.tsx         # Camera dynamique suivant le locuteur
│   │       └── SceneLighting.tsx     # Eclairage atmospherique
│   ├── hooks/
│   │   ├── useGameState.tsx          # Etat central du jeu + consommateur SSE
│   │   ├── useVoice.ts              # File TTS + Scribe STT
│   │   └── useBackgroundAudio.ts    # Musique de phase + attenuation TTS
│   └── lib/
│       ├── api.ts                    # Appels API + parseurs de flux SSE
│       ├── game-types.ts            # Types TypeScript (26 types d'evenements)
│       └── scene-constants.ts       # Geometrie 3D + presets camera
│
├── run.py                            # Lanceur du serveur backend
└── requirements.txt                  # Dependances Python
```

---

## ✦ Fondements de recherche

L'intelligence des agents de COUNCIL est ancree dans la recherche publiee sur les jeux multi-agents :

| Fondement | Application dans COUNCIL |
|-----------|-------------------------|
| **Pipeline SSRSR** (xuyuzhuang-Werewolf) | Competence Raisonnement strategique : Situation → Soupçons → Reflexion → Strategie → Reponse — cognition structuree de pre-reponse |
| **Heuristiques role-strategie** (LLMWereWolf) | Competence Maitrise de la tromperie : strategies comportementales conditionnees par faction — les agents du mal/bien reçoivent des directives fondamentalement differentes |
| **Circomplexe interpersonnel de Leary** | Systeme de personnalite Mind Mirror : 4 plans de pensee (bio, emotionnel, mental, social) generant un « jazz » comportemental unique |
| **Modele de personnalite Sims** | 5 traits avec un budget de 25 points (ordre/sociabilite/activite/jeu/gentillesse) modulant les probabilites et defauts emotionnels |
| **Big Five + MBTI** | ADN de personnalite multidimensionnel garantissant un comportement de personnage diversifie et psychologiquement fonde |
| **Apprentissage contrastif** | Exemples comportementaux bons/mauvais en contexte enseignant aux agents un jeu de qualite par la demonstration |

---

## ✦ Licence

Ce projet est sous licence [MIT](LICENSE).

---

<div align="center">

**Construit pour le [Mistral AI Worldwide Hackathon 2026](https://mistral.ai/)**

<a href="https://mistral.ai"><img src="https://img.shields.io/badge/Mistral_AI-FA520F?style=for-the-badge&logo=mistralai&logoColor=white" alt="Mistral AI"/></a>
<a href="https://elevenlabs.io"><img src="https://img.shields.io/badge/ElevenLabs-000000?style=for-the-badge&logo=elevenlabs&logoColor=white" alt="ElevenLabs"/></a>
<a href="https://supabase.com"><img src="https://img.shields.io/badge/Supabase-3FCF8E?style=for-the-badge&logo=supabase&logoColor=white" alt="Supabase"/></a>
<a href="https://upstash.com"><img src="https://img.shields.io/badge/Upstash-00E9A3?style=for-the-badge&logo=upstash&logoColor=white" alt="Upstash"/></a>

</div>
