#!/usr/bin/env python3
"""
Injection du curriculum Anglais A1→C2 — version complète et affinée
Généré par Claude Code / Claude Sonnet — 2026-04-05

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEPRECATED (Session 37, 2026-04-21) — use scripts/inject_curriculum.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This script hardcodes the EN curriculum as a 600-line Python dict, writes to
legacy `points_cles` column only, and doesn't populate the normalized
concept_keys/weights/groups. Session 37 introduced a YAML-driven replacement:

    python3 scripts/inject_curriculum.py --domain en --force

The `--force` flag is required because curriculum_en.yaml (53 concepts) may
drift from the current DB state (18+ concept_keys per level after Sprint 2-3
+ inject_concept_keys.py augmentation). Manually reconcile before re-running.

This file is KEPT for historical reference and as a fallback should the YAML
migration go wrong. Do NOT run it as part of normal operations — it will
silently overwrite `points_cles` with legacy data.
"""

import os
import json
import psycopg2
from pathlib import Path

def _read_secret(name, fallback=""):
    p = Path(f"/opt/academie-shared/secrets/{name}")
    return p.read_text().strip() if p.exists() else fallback

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "172.16.0.19"),
    "port": int(os.environ.get("DB_PORT", "5432")),
    "dbname": os.environ.get("DB_NAME", "academie_db"),
    "user": os.environ.get("DB_USER", "sinse"),
    "password": os.environ.get("DB_PASSWORD", _read_secret("pg-password")),
}

CURRICULUM = [
    # ─────────────────────────────────────────────
    # A1 — SURVIE
    # ─────────────────────────────────────────────
    {
        "domaine": "anglais",
        "niveau": "A1",
        "description": "Niveau introductif (Survie) — L'apprenant peut comprendre et utiliser des expressions familières et quotidiennes ainsi que des énoncés très simples visant à satisfaire des besoins concrets.",
        "points_cles": {
            "grammaire": [
                "Verbe 'to be' : formes affirmative, négative, interrogative (I am, you are, he is...)",
                "Verbe 'to have got' : possession (I have got / I've got)",
                "Present simple : verbes d'état et routines (I live, she works)",
                "Pronoms personnels sujets (I, you, he, she, it, we, they)",
                "Pronoms personnels compléments (me, you, him, her, it, us, them)",
                "Adjectifs possessifs (my, your, his, her, its, our, their)",
                "Articles défini (the) et indéfinis (a, an) — règles de base",
                "Pluriels réguliers (cat→cats, box→boxes, baby→babies)",
                "Adjectifs qualificatifs : position avant le nom, invariabilité",
                "Démonstratifs : this / that / these / those",
                "Questions avec mots interrogatifs simples : Who, What, Where, When, How old",
                "Réponses courtes : Yes, I am / No, it isn't",
                "Prépositions de lieu basiques : in, on, at, under, next to",
                "Prépositions de temps : at (heure), on (jour), in (mois/année)",
                "There is / There are : existence",
                "Impératif : ordres simples (Sit down! Don't run!)",
                "Nombres cardinaux 0–1000",
                "Nombres ordinaux 1st–31st (dates)",
            ],
            "vocabulaire": {
                "thèmes": [
                    "Salutations et présentations (Hello, Hi, Nice to meet you, Goodbye)",
                    "Identité : nom, prénom, nationalité, âge, adresse",
                    "Famille proche (mother, father, brother, sister, son, daughter)",
                    "Corps humain (head, eyes, hands, legs...)",
                    "Couleurs (red, blue, green, dark, light...)",
                    "Vêtements courants (shirt, jeans, dress, shoes)",
                    "Nourriture et boissons de base (bread, water, coffee, apple)",
                    "Nombres, jours de la semaine, mois, saisons",
                    "Heure (It's three o'clock / half past two)",
                    "Lieux courants (school, home, shop, station, hospital)",
                    "Objets du quotidien (phone, book, bag, key, table)",
                    "Animaux communs (dog, cat, bird, fish)",
                    "Professions de base (teacher, doctor, student, chef)",
                    "Actions quotidiennes (eat, drink, sleep, go, come, work)",
                ],
                "volume_cible": "500–700 mots"
            },
            "phonologie": [
                "Alphabet anglais — prononciation de chaque lettre",
                "Sons voyelles courts vs longs (/ɪ/ vs /iː/, /ʊ/ vs /uː/)",
                "Distinction /θ/ et /ð/ (think, this) — absent en français",
                "Liaison et élision naturelle dans les formules de salutation",
                "Accentuation des mots bisyllabiques communs (TEAcher, sTUdent)",
                "Intonation montante en questions fermées (Are you French?↗)",
            ],
            "competences": {
                "comprehension_orale": [
                    "Comprendre son prénom et sa nationalité quand on lui demande",
                    "Saisir des instructions simples (Open the door, Sit down)",
                    "Comprendre des nombres, prix, heures énoncés clairement",
                ],
                "expression_orale": [
                    "Se présenter : nom, âge, nationalité, ville",
                    "Épeler son nom lettre par lettre",
                    "Demander et donner l'heure",
                    "Commander un plat ou une boisson simple",
                ],
                "comprehension_ecrite": [
                    "Lire des panneaux, étiquettes, formulaires simples",
                    "Comprendre un SMS ou message très court",
                    "Saisir les informations d'une carte de visite",
                ],
                "expression_ecrite": [
                    "Remplir un formulaire d'identité",
                    "Écrire un message court (3-4 phrases) pour se présenter",
                    "Rédiger une liste de courses simple",
                ],
            },
            "erreurs_communes": [
                "Oublier le 's' à la 3ème personne du singulier (she go → she goes)",
                "Confondre 'he' et 'she' (interférence selon L1)",
                "Utiliser 'the' devant les noms propres (the France → France)",
                "Dire 'I am agree' au lieu de 'I agree'",
                "Oublier l'auxiliaire dans les questions (You like it? → Do you like it?)",
                "Traduction littérale de 'j'ai X ans' → 'I have 20 years' (→ I am 20)",
            ],
            "objectifs_cecrl": [
                "Peut se présenter et présenter quelqu'un",
                "Peut poser des questions sur des données personnelles et répondre aux mêmes",
                "Peut interagir simplement si l'interlocuteur parle lentement et distinctement",
                "Peut utiliser des expressions et des phrases simples pour décrire son lieu d'habitation",
            ],
            "concepts_nouveaux_vs_niveau_precedent": "Niveau fondateur — toutes les structures sont nouvelles"
        }
    },

    # ─────────────────────────────────────────────
    # A2 — QUOTIDIEN
    # ─────────────────────────────────────────────
    {
        "domaine": "anglais",
        "niveau": "A2",
        "description": "Niveau élémentaire (Quotidien) — L'apprenant peut communiquer lors de tâches simples et habituelles, décrire son environnement immédiat et exprimer des besoins immédiats.",
        "points_cles": {
            "grammaire": [
                "Present simple : usage complet (habitudes, vérités générales, horaires)",
                "Present continuous : actions en cours, projets proches (I'm leaving tomorrow)",
                "Past simple régulier : -ed et règles orthographiques",
                "Past simple irrégulier : 60 verbes irréguliers fréquents",
                "Past continuous : action en cours dans le passé (was/were + -ing)",
                "Future avec 'going to' : intentions et prévisions",
                "Future avec 'will' : décisions spontanées, promesses, prédictions",
                "Comparatifs : réguliers (bigger, more interesting) et irréguliers (better, worse)",
                "Superlatifs : réguliers (the biggest) et irréguliers (the best)",
                "Modaux de base : can/can't (capacité), must/mustn't (obligation), should (conseil)",
                "Modaux de permission : can/could/may",
                "Questions indirectes simples (Can you tell me where the station is?)",
                "Some / any / no : règles d'emploi en affirmatif/négatif/interrogatif",
                "Much / many / a lot of / a few / a little",
                "Adverbes de fréquence (always, usually, often, sometimes, rarely, never) et leur position",
                "Propositions relatives simples avec 'who' et 'which/that'",
                "Prépositions de mouvement : to, from, into, out of, through, along",
                "Conjonctions de base : because, so, but, although, when, if",
                "Questions tags simples (It's nice, isn't it?)",
            ],
            "vocabulaire": {
                "thèmes": [
                    "Travail et professions (interview, salary, colleague, boss, office)",
                    "Loisirs et activités (hobby, match, concert, cinema, gym)",
                    "Sports et activités physiques",
                    "Voyages et transports (ticket, platform, delay, passport, customs)",
                    "Météo et saisons (sunny, cloudy, freezing, forecast)",
                    "Achats et commerce (price, discount, receipt, size, refund)",
                    "Santé et corps (symptom, appointment, medicine, pharmacy)",
                    "Maison et logement (bedroom, kitchen, rent, furniture, neighbour)",
                    "Alimentation avancée (recipe, ingredient, taste, allergies)",
                    "Sorties et vie sociale (invitation, celebration, party)",
                    "Banque et argent (account, withdrawal, currency, bill)",
                    "Technologies de base (computer, password, internet, app)",
                    "Description physique et personnalité (tall, shy, generous, stubborn)",
                ],
                "volume_cible": "1000–1500 mots"
            },
            "phonologie": [
                "Sons /æ/ (cat), /ʌ/ (cup), /ɜː/ (bird) — distinctions clés",
                "Prononciation du '-ed' final : /t/, /d/, /ɪd/ selon le contexte",
                "Liaisons : 'going to' → /ˈɡənə/ (gonna), 'want to' → /ˈwɒnə/ (wanna)",
                "Distinction entre le 'l' vocalique ('little') et consonantique ('let')",
                "Accentuation des phrases : mots de contenu vs mots outils",
                "Intonation descendante sur les questions ouvertes (Where do you live?↘)",
            ],
            "competences": {
                "comprehension_orale": [
                    "Comprendre des annonces courtes et claires (gare, aéroport)",
                    "Saisir l'essentiel d'une conversation sur des sujets familiers",
                    "Comprendre des instructions simples données par un professeur ou collègue",
                ],
                "expression_orale": [
                    "Raconter une journée ou un événement passé simple",
                    "Parler de ses goûts, loisirs et habitudes",
                    "Donner des directions basiques dans une ville",
                    "Décrire une personne ou un objet",
                ],
                "comprehension_ecrite": [
                    "Lire des messages personnels courts (email, SMS)",
                    "Comprendre un menu de restaurant ou une publicité simple",
                    "Saisir les informations principales d'un article très court",
                ],
                "expression_ecrite": [
                    "Écrire une carte postale ou un message de remerciement",
                    "Rédiger un email informel court (invitation, excuse)",
                    "Compléter un formulaire détaillé",
                ],
            },
            "erreurs_communes": [
                "Confusion present simple / present continuous (I am going to work every day → I go)",
                "Oublier les formes irrégulières du past simple (goed → went, thinked → thought)",
                "Mal positionner les adverbes de fréquence (He goes always → He always goes)",
                "Confondre 'much' et 'many' (much people → many people)",
                "Employer 'will' pour toutes les formes du futur (au lieu de 'going to' pour les intentions)",
                "Interférence 'since'/'for' : 'I'm here since 3 years' → 'I've been here for 3 years'",
                "Oublier '-ing' après les prépositions (after eat → after eating)",
            ],
            "objectifs_cecrl": [
                "Peut communiquer lors de tâches simples et habituelles",
                "Peut décrire avec des moyens simples sa formation, son environnement immédiat",
                "Peut comprendre des expressions liées à des domaines de priorité immédiate",
                "Peut utiliser des séries d'expressions et phrases pour décrire sa famille",
            ],
            "concepts_nouveaux_vs_niveau_precedent": [
                "Past simple (régulier + irrégulier)",
                "Present et past continuous",
                "Futur avec 'going to' et 'will'",
                "Comparatifs et superlatifs",
                "Modaux de base (must, should)",
                "Some/any/much/many",
            ]
        }
    },

    # ─────────────────────────────────────────────
    # B1 — AUTONOMIE
    # ─────────────────────────────────────────────
    {
        "domaine": "anglais",
        "niveau": "B1",
        "description": "Niveau seuil (Autonomie) — L'apprenant peut se débrouiller dans la plupart des situations rencontrées en voyage, produire un discours simple et cohérent sur des sujets familiers et exprimer des expériences, événements, espoirs ou ambitions.",
        "points_cles": {
            "grammaire": [
                "Present perfect simple : expériences (have you ever?), résultats présents (I've lost my keys)",
                "Present perfect vs past simple : distinction cruciale (I've seen vs I saw yesterday)",
                "Present perfect continuous : durée jusqu'au présent (I've been waiting for an hour)",
                "Past perfect : antériorité dans le passé (When I arrived, she had left)",
                "Voix passive : tous les temps de base (is made, was built, has been cancelled)",
                "Conditionnel 1 (réel) : If + present simple → will + infinitif",
                "Conditionnel 2 (hypothétique) : If + past simple → would + infinitif",
                "Verbes modaux de déduction : must be, might be, can't be (présent)",
                "Discours rapporté de base : say/tell + that, asked/told + infinitif",
                "Questions indirectes complètes (Could you tell me how much it costs?)",
                "Phrasal verbs fréquents (give up, look after, find out, get on with, turn off)",
                "Gérondif vs infinitif après les verbes courants (enjoy + -ing, want + to)",
                "Adjectifs + prépositions (interested in, good at, afraid of, happy about)",
                "Adverbes de degré (quite, rather, fairly, extremely, absolutely)",
                "Used to + infinitif : habitudes passées révolues",
                "Would + infinitif : habitudes passées (narrative)",
                "So / such... that : conséquence",
                "Clauses relatives définissantes et non-définissantes (who, which, that, whose, where)",
                "Connecteurs logiques : however, therefore, although, despite, in spite of, as a result",
                "Both, either, neither",
            ],
            "vocabulaire": {
                "thèmes": [
                    "Voyages et tourisme (sightseeing, accommodation, itinerary, budget)",
                    "Éducation et formation (course, degree, qualification, dissertation, dropout)",
                    "Environnement et nature (pollution, climate change, endangered species, carbon footprint)",
                    "Médias et actualités (headline, broadcast, journalist, social media, fake news)",
                    "Sentiments et émotions (frustrated, relieved, anxious, overwhelmed, content)",
                    "Santé et bien-être (symptoms, diagnosis, prescription, therapy, recovery)",
                    "Relationships (friendship, loyalty, trust, argument, reconciliation)",
                    "Travail (promotion, resignation, meeting, deadline, teamwork)",
                    "Argent et finances personnelles (budget, debt, savings, mortgage, investment)",
                    "Phrasal verbs courants (100 les plus fréquents)",
                    "Collocations de base (make a decision, do homework, take a break)",
                    "Faux amis fréquents (eventually ≠ éventuellement, actually ≠ actuellement)",
                ],
                "volume_cible": "2500–3500 mots"
            },
            "phonologie": [
                "Weak forms : 'the' → /ðə/, 'and' → /ən/, 'can' → /kən/ en débit normal",
                "Assimilation consonantique (good boy → /ɡʊb bɔɪ/)",
                "Schwa /ə/ : le son le plus fréquent de l'anglais (about, letter, forgotten)",
                "Elision (next day → /neks deɪ/, most people → /məʊs ˈpiːpəl/)",
                "Différences de prononciation UK vs US sur les mots courants",
                "Rythme accentuel de l'anglais vs syllabique du français",
            ],
            "competences": {
                "comprehension_orale": [
                    "Comprendre l'essentiel d'émissions TV ou radio sur des sujets d'actualité",
                    "Suivre les points principaux d'une conférence ou exposé sur des sujets familiers",
                    "Comprendre une conversation entre locuteurs natifs si le sujet est connu",
                ],
                "expression_orale": [
                    "Raconter une histoire ou un film en détaillant réactions et opinions",
                    "Participer à une conversation sur des sujets familiers sans préparation",
                    "Justifier et expliquer brièvement ses opinions",
                    "Faire face à la plupart des situations lors d'un séjour en pays anglophone",
                ],
                "comprehension_ecrite": [
                    "Lire des textes factuels sur des sujets de son domaine de compétence",
                    "Comprendre la description d'événements, sentiments dans une lettre personnelle",
                    "Saisir les arguments principaux d'un article de presse",
                ],
                "expression_ecrite": [
                    "Écrire un texte simple et cohérent sur des sujets familiers",
                    "Rédiger une lettre ou email personnel (expériences, actualités, projets)",
                    "Écrire un compte-rendu ou résumé simple",
                ],
            },
            "erreurs_communes": [
                "Confusion present perfect / past simple (I have seen him yesterday → I saw him)",
                "Mal employer la voix passive (The book was written by him easily → The book was easily written)",
                "Oublier 'to' dans les questions indirectes (Could you tell me where is the station → where the station is)",
                "Confondre 'say' et 'tell' au discours rapporté",
                "Utiliser 'since' au lieu de 'for' avec une durée (since 3 years → for 3 years)",
                "Mal conjuguer le conditionnel 2 (If I would have → If I had)",
                "Gérondif vs infinitif : I enjoy to swim → I enjoy swimming",
            ],
            "objectifs_cecrl": [
                "Peut comprendre les points essentiels quand un langage clair est utilisé sur des sujets familiers",
                "Peut se débrouiller dans la plupart des situations lors d'un voyage en région anglophone",
                "Peut produire un discours simple et cohérent sur des sujets familiers",
                "Peut écrire un texte simple et cohérent sur des sujets familiers",
                "Peut décrire des expériences, des événements, des espoirs et des ambitions",
            ],
            "concepts_nouveaux_vs_niveau_precedent": [
                "Present perfect (simple et continuous) vs past simple",
                "Past perfect",
                "Conditionnel 1 & 2",
                "Voix passive",
                "Modaux de déduction",
                "Discours rapporté",
                "Phrasal verbs systématiques",
            ]
        }
    },

    # ─────────────────────────────────────────────
    # B2 — AISANCE
    # ─────────────────────────────────────────────
    {
        "domaine": "anglais",
        "niveau": "B2",
        "description": "Niveau avancé (Aisance) — L'apprenant peut comprendre le contenu essentiel de sujets concrets ou abstraits dans un texte complexe, communiquer avec un degré de spontanéité et s'exprimer de façon claire et détaillée sur une large gamme de sujets.",
        "points_cles": {
            "grammaire": [
                "Conditionnel 3 (irréel passé) : If + past perfect → would have + past participle",
                "Mixed conditionals : If + past perfect → would + infinitif (et vice versa)",
                "Modaux de déduction au passé : must have, might have, can't have, could have",
                "Modaux de reproche / regret : should have, needn't have, ought to have",
                "Discours rapporté complet : backshift, pronoms, expressions de temps",
                "Voix passive avancée : have something done, get something done, passif avec modaux",
                "Inversion avec adverbes négatifs : Never have I..., Not only did..., Hardly had...",
                "Emphase : cleft sentences (It was John who..., What I need is...)",
                "Subjonctif passé dans les souhaits : I wish / If only + past perfect",
                "I wish + would : irritation (I wish you would stop!)",
                "Clauses de participe (Having finished the report, she left. / Not knowing what to do...)",
                "Structures causatives complexes (have/get sb to do sth, make sb do sth)",
                "Adjectifs composés (well-known, thought-provoking, state-of-the-art)",
                "Préfixes et suffixes productifs (dis-, un-, -tion, -ness, -ity, -ful, -less)",
                "Articles avec abstractions, généralisations, noms propres — nuances avancées",
                "Propositions relatives réduites (The man speaking to her is my boss)",
                "Connecteurs sophistiqués : nevertheless, whereas, provided that, as long as, given that",
                "Structures parallèles et coordination équilibrée",
            ],
            "vocabulaire": {
                "thèmes": [
                    "Monde du travail et business (negotiation, stakeholder, merger, turnover, KPI)",
                    "Technologie et innovation (AI, automation, blockchain, disruption, scalability)",
                    "Sciences et recherche (hypothesis, methodology, peer review, findings)",
                    "Arts, littérature et culture (narrative, symbolism, genre, interpretation)",
                    "Politique et société (legislation, referendum, lobby, civil rights, inequality)",
                    "Économie (recession, inflation, GDP, fiscal policy, trade deficit)",
                    "Psychologie et comportement (cognitive bias, motivation, resilience)",
                    "Collocations avancées (make a significant contribution, raise awareness, draw a conclusion)",
                    "Expressions idiomatiques de niveau B2 (hit the nail on the head, bite off more than you can chew)",
                    "Registres formels vs informels — début de maîtrise",
                    "Vocabulary building : word families, collocations, connotations",
                    "Faux-amis avancés et nuances sémantiques",
                ],
                "volume_cible": "5000–7000 mots"
            },
            "phonologie": [
                "Maîtrise des contractions naturelles en débit rapide (would've, should've, I'd have)",
                "Liaison et enchaînement dans des phrases complexes",
                "Accentuation des mots dérivés et composés (PHOtograph → phoTOgraphy → photoGRAPHic)",
                "Intonation pour exprimer nuance, surprise, ironie, emphase",
                "Compréhension d'accents variés (irlandais, australien, américain, indien)",
            ],
            "competences": {
                "comprehension_orale": [
                    "Comprendre des émissions TV, films, podcasts en anglais natif (avec effort)",
                    "Saisir les arguments et contre-arguments dans un débat",
                    "Comprendre des conférences longues sur son domaine de compétence",
                ],
                "expression_orale": [
                    "S'exprimer avec spontanéité sur des sujets abstraits",
                    "Défendre un point de vue et concéder des arguments",
                    "Présenter un exposé structuré avec introduction, développement, conclusion",
                    "Participer activement à des discussions sur des sujets d'actualité",
                ],
                "comprehension_ecrite": [
                    "Lire des articles de presse, des rapports et des textes académiques courants",
                    "Comprendre un roman contemporain (avec quelques inconnues)",
                    "Analyser l'argument principal et les arguments secondaires d'un texte",
                ],
                "expression_ecrite": [
                    "Rédiger une dissertation argumentée (for/against, discursive essay)",
                    "Écrire un rapport ou une lettre formelle professionnelle",
                    "Résumer un texte long en conservant les points clés",
                    "Rédiger une critique (film, livre, produit)",
                ],
            },
            "erreurs_communes": [
                "Confondre conditionnel 2 et 3 (If I had known → If I would have known)",
                "Mal maîtriser la backshift au discours rapporté (He said he will → he would)",
                "Inverser sans déclencheur approprié (Never I have seen → Never have I seen)",
                "Confondre 'must have been' (déduction) et 'had to be' (obligation passée)",
                "Construire incorrectement les cleft sentences (It was where he met → It was there that he met)",
                "Lexique : utiliser le mot exact mais sans la bonne collocation (make/do/take errors)",
            ],
            "objectifs_cecrl": [
                "Peut comprendre des textes complexes sur des sujets concrets ou abstraits",
                "Peut communiquer avec spontanéité et aisance avec un locuteur natif",
                "Peut s'exprimer de façon claire et détaillée sur une large gamme de sujets",
                "Peut émettre un avis sur un sujet d'actualité en indiquant avantages et inconvénients",
                "Peut produire un texte clair et détaillé sur des sujets relatifs à son domaine d'intérêt",
            ],
            "concepts_nouveaux_vs_niveau_precedent": [
                "Conditionnel 3 et mixed conditionals",
                "Modaux au passé (must have, should have, etc.)",
                "Inversion et emphase",
                "Cleft sentences",
                "Discours rapporté complet avec backshift",
                "Maîtrise active des registres",
                "Collocations avancées",
            ]
        }
    },

    # ─────────────────────────────────────────────
    # C1 — MAÎTRISE
    # ─────────────────────────────────────────────
    {
        "domaine": "anglais",
        "niveau": "C1",
        "description": "Niveau autonome avancé (Maîtrise) — L'apprenant peut s'exprimer spontanément et couramment sans trop chercher ses mots, utiliser la langue de façon efficace et souple dans sa vie sociale, académique et professionnelle.",
        "points_cles": {
            "grammaire": [
                "Nominalisation complexe : transformer des structures verbales en noms (the government's refusal to act, his reluctance to concede)",
                "Inversion stylistique avancée : Not until, Only when, So + adj. + that",
                "Subjonctif formel présent : It is essential that he be informed, I suggest she attend",
                "Ellipse et substitution : I think so / I hope not / so do I / neither can she",
                "Deixis et cohésion textuelle : this/that en référence anaphorique et cataphorique",
                "Structures de topicalisation : As for the budget, this remains unclear",
                "Modaux à valeur stylistique : will (habitude/caractère), would (distanciation polie)",
                "Conditionnels implicites sans 'if' : Had he known..., Were it not for..., Should you need...",
                "Discours rapporté avec verbes de reporting nuancés (alleged, maintained, conceded, urged)",
                "Gradation stylistique : structures de plus en plus, de moins en moins complexes",
                "Distanciation et hedging académique : It appears that, It could be argued that, It would seem",
                "Gérondifs sujets complexes (Implementing such a policy requires careful planning)",
                "Constructions absolues : Weather permitting, All things considered, Other things being equal",
                "Maîtrise totale de l'aspect (simple/continuous/perfect) avec nuance stylistique",
            ],
            "vocabulaire": {
                "thèmes": [
                    "Idiomes et expressions métaphoriques en contexte (turn a blind eye, the tip of the iceberg)",
                    "Vocabulaire académique (OPAL/AWL) : hypothesis, paradigm, constitute, framework, principle",
                    "Nuances sémantiques fines (gaze/glance/stare, walk/stride/stroll/trudge)",
                    "Vocabulaire professionnel multi-domaine (droit, médecine, finance, tech)",
                    "Connotations culturelles : understatement britannique, directness américaine",
                    "Faux-amis rares et subtils (comprehensive ≠ compréhensif, assist ≠ assister à)",
                    "Phrasal verbs et prépositional verbs peu fréquents (conjure up, veer off, reign in)",
                    "Affixes productifs avancés (-ize/-ise, -ify, hyper-, pseudo-, proto-)",
                    "Lexique des émotions complexes (ambivalence, dissonance, exhilaration, schadenfreude)",
                    "Rhétorique et discours : rhetorical question, anaphore, litote, euphémisme",
                ],
                "volume_cible": "10 000+ mots actifs, 15 000+ passifs"
            },
            "phonologie": [
                "Naturalisation du débit : connected speech, réduction syllabique spontanée",
                "Capacité à adapter son accent (intelligibilité internationale vs RP vs GA)",
                "Maîtrise de l'intonation pragmatique : sarcasme, emphase, nuance, hésitation",
                "Compréhension d'accents non-standard (scots, nigerian english, singaporean english)",
                "Reconnaître et produire les glottalisations et flaps américains (water /ˈwɔːɾər/)",
            ],
            "competences": {
                "comprehension_orale": [
                    "Comprendre des émissions en anglais natif sans effort notable",
                    "Identifier sous-entendus, ironie et humour culturel",
                    "Suivre une conversation rapide entre plusieurs locuteurs natifs",
                ],
                "expression_orale": [
                    "S'exprimer couramment sur des sujets complexes et abstraits",
                    "Utiliser la langue de façon flexible à des fins sociales, académiques et professionnelles",
                    "Formuler des idées et des opinions avec précision, nuance et cohérence",
                    "Négocier, persuader, débattre avec des locuteurs natifs",
                ],
                "comprehension_ecrite": [
                    "Comprendre des textes longs et complexes : littérature, presse de qualité, rapports",
                    "Identifier la structure argumentative, les présupposés et les implicites",
                    "Saisir les nuances stylistiques et rhétoriques d'un auteur",
                ],
                "expression_ecrite": [
                    "Rédiger des textes clairs, bien structurés et détaillés sur des sujets complexes",
                    "Écrire dans un style approprié au lecteur et à l'objectif visé",
                    "Synthétiser des informations de sources multiples",
                    "Rédiger un essai académique, un rapport professionnel ou un article",
                ],
            },
            "erreurs_communes": [
                "Employer le subjonctif formel hors contexte approprié (registre)",
                "Suremployer les idiomes (forcer l'effet naturel)",
                "Nominalisation excessive → lourdeur stylistique",
                "Hedging insuffisant dans les écrits académiques",
                "Confondre les nuances des synonymes précis (policy vs politics vs politeness)",
                "Ignorer les collocations figées au profit de constructions logiques mais fausses",
            ],
            "objectifs_cecrl": [
                "Peut comprendre une large gamme de textes longs et exigeants",
                "Peut s'exprimer spontanément et couramment sans trop chercher ses mots",
                "Peut utiliser la langue de façon efficace et souple dans sa vie sociale, académique et professionnelle",
                "Peut produire des textes clairs, bien structurés et détaillés sur des sujets complexes",
            ],
            "concepts_nouveaux_vs_niveau_precedent": [
                "Nominalisation stylistique",
                "Conditionnels inversés (Had he known...)",
                "Subjonctif formel",
                "Hedging et distanciation académique",
                "Constructions absolues",
                "Maîtrise active des registres (formel/neutre/informel/argot)",
                "Pragmatique et inférence",
            ]
        }
    },

    # ─────────────────────────────────────────────
    # C2 — EXCELLENCE
    # ─────────────────────────────────────────────
    {
        "domaine": "anglais",
        "niveau": "C2",
        "description": "Niveau de maîtrise (Excellence) — L'apprenant peut comprendre sans effort pratiquement tout ce qu'il lit ou entend, restituer faits et arguments avec précision, et s'exprimer spontanément, très couramment et précisément en distinguant les nuances de sens les plus fines.",
        "points_cles": {
            "grammaire": [
                "Flexibilité totale entre tous les temps et aspects — choix stylistique conscient",
                "Manipulation rhétorique des structures : anaphore, tricolon, chiasme grammatical",
                "Jeu avec les attentes normatives pour créer des effets stylistiques",
                "Maîtrise des archaïsmes et formes littéraires (thou, hath, 'tis) en contexte",
                "Utilisation créative de la ponctuation et de la syntaxe fragmentée",
                "Code-switching stylistique fluide entre registres selon l'audience",
                "Maîtrise du discours indirect libre (literary free indirect discourse)",
                "Structures de coordination et subordination d'une complexité illimitée",
                "Méta-conscience grammaticale : pouvoir expliquer et enseigner toute règle",
                "Pragmatique : actes de langage indirects, implicatures conversationnelles (Grice)",
            ],
            "vocabulaire": {
                "thèmes": [
                    "Répertoire exhaustif d'expressions idiomatiques tous registres confondus",
                    "Nuances de connotations positives/négatives/neutres entre synonymes proches",
                    "Résonances culturelles et historiques des mots (loaded language, dog-whistle terms)",
                    "Argot et vernaculaire contemporain (AAVE, British slang, internet slang) avec conscience sociolinguistique",
                    "Néologismes et créations lexicales contemporaines",
                    "Vocabulaire spécialisé profond dans au moins un domaine",
                    "Jeux de mots, paronomases, calembours — production et compréhension",
                    "Précision maximale : le mot exact pour chaque situation (compendium ≠ summary ≠ digest ≠ overview)",
                    "Register awareness totale : connaître le niveau de formalité de chaque mot",
                ],
                "volume_cible": "20 000+ mots actifs (comparable à un natif instruit)"
            },
            "phonologie": [
                "Intelligibilité dans plusieurs accents sans effort",
                "Capacité à imiter et adopter consciemment des accents (UK/US/autres) si nécessaire",
                "Contrôle parfait de la prosodie : débit, pauses, emphase pour l'effet oratoire",
                "Compréhension de dialectes éloignés (Geordie, Deep South US, Caribbean Creole)",
                "Utilisation de la voix comme outil rhétorique (débit, volume, timbre)",
            ],
            "competences": {
                "comprehension_orale": [
                    "Comprendre sans effort tout document audio/vidéo en anglais natif",
                    "Saisir humour subtil, sous-entendus culturels, intertextualité",
                    "Comprendre des dialectes, accents marqués et parlers populaires",
                ],
                "expression_orale": [
                    "S'exprimer de manière indistinguable d'un locuteur natif instruit dans le domaine de son choix",
                    "Maîtriser l'art oratoire : persuasion, narration, improvisation",
                    "Adapter son registre, son rythme et son style à n'importe quel interlocuteur",
                    "Créer et raconter de l'humour culturellement ancré",
                ],
                "comprehension_ecrite": [
                    "Comprendre et apprécier la littérature anglophone dans sa complexité stylistique",
                    "Analyser des textes juridiques, scientifiques, philosophiques",
                    "Identifier la manipulation du langage, la propagande, les biais rhétoriques",
                ],
                "expression_ecrite": [
                    "Écrire dans n'importe quel genre et registre avec maîtrise stylistique",
                    "Créer des textes littéraires, persuasifs, académiques d'une qualité équivalente à celle d'un natif",
                    "Maîtriser l'éditing : reformuler, condenser, amplifier un texte selon les besoins",
                ],
            },
            "erreurs_communes": [
                "Sur-correction : éviter l'anglais spontané par peur de l'erreur",
                "Calques syntaxiques très subtils du français dans des phrases complexes",
                "Manque de naturalité dans l'humour ou les références culturelles",
                "Utilisation correcte mais non-native des collocations ultra-idiomatiques",
                "Méconnaissance des dialectes et sous-cultures linguistiques",
            ],
            "objectifs_cecrl": [
                "Peut comprendre sans effort pratiquement tout ce qu'il entend ou lit",
                "Peut restituer faits et arguments de diverses sources écrites et orales",
                "Peut s'exprimer spontanément, très couramment et de façon précise",
                "Peut différencier de fines nuances de sens en rapport avec des sujets complexes",
            ],
            "dimensions_culturelles": [
                "Understatement britannique et dry humour",
                "Directness américaine vs indirectness britannique",
                "Political correctness et évolution du lexique en contexte anglo-saxon",
                "Références littéraires et culturelles canoniques (Shakespeare, Bible, pop culture)",
                "Soft power de l'anglais : diversité des englishes dans le monde (World Englishes)",
            ],
            "concepts_nouveaux_vs_niveau_precedent": [
                "Flexibilité stylistique totale et consciente",
                "Rhétorique et oratoire",
                "Pragmatique avancée (implicatures, actes de langage indirects)",
                "Sociolinguistique : variation, registres, dialectes",
                "Méta-conscience : pouvoir analyser et enseigner la langue",
                "Dimension culturelle profonde",
            ]
        }
    },
]


def inject_curriculum():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    success = 0
    for entry in CURRICULUM:
        cur.execute(
            """
            INSERT INTO curriculums (domaine, niveau, description, points_cles)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (domaine, niveau) DO UPDATE
              SET description = EXCLUDED.description,
                  points_cles = EXCLUDED.points_cles
            """,
            (
                entry["domaine"],
                entry["niveau"],
                entry["description"],
                json.dumps(entry["points_cles"], ensure_ascii=False),
            ),
        )
        print(f"  ✅ {entry['domaine'].upper()} {entry['niveau']} — injecté")
        success += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"\n🎓 Curriculum injecté : {success}/6 niveaux")


if __name__ == "__main__":
    inject_curriculum()
