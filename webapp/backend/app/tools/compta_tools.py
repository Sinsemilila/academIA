"""S57 — Tools fonctionnels pour Maître Comptable Phase 1 Mode B.

Détection rules-first 80% / LLM 20% (cf ADR-017 D3). Ces tools sont appelés
par le chatflow Dify via tool calling — déterministes, pas d'hallucination.

Tools exposés :
- lookup_pcg_account(num) → libellé PCG + classe
- verify_partie_double(ecritures) → True/False + diff + détail
- verify_calcul_tva(montant_ht, taux, expected_tva, expected_ttc) → check exhaustif
- verify_compte_classe(num, expected_classe) → check si compte appartient à classe
- lookup_studi_module(query) → mapping concept → module Studi BC1.X (Phase 2 stub)

Pattern réutilisable Phase 2+ pour autres domaines fermés.
"""
from __future__ import annotations

from typing import TypedDict

from .compta_pcg import (
    PCG_CLASSES,
    PCG_MAIN_ACCOUNTS,
    TVA_TAUX_STANDARD,
)


class EcritureLine(TypedDict):
    """Une ligne d'écriture comptable."""
    compte: str
    libelle: str
    debit: float
    credit: float


class PCGLookupResult(TypedDict):
    """Résultat lookup_pcg_account."""
    found: bool
    compte: str
    libelle: str
    classe: str
    classe_libelle: str
    detail: str  # message pour LLM
    suggestions: list[str]  # comptes proches si pas trouvé


class PartieDoubleResult(TypedDict):
    """Résultat verify_partie_double."""
    valid: bool
    sum_debits: float
    sum_credits: float
    diff: float  # debits - credits
    n_lines: int
    detail: str  # message pour LLM (français)


class TVAVerifyResult(TypedDict):
    """Résultat verify_calcul_tva."""
    valid: bool
    montant_ht: float
    taux: float
    expected_tva: float
    expected_ttc: float
    actual_tva: float | None
    actual_ttc: float | None
    taux_valide: bool
    detail: str


def lookup_pcg_account(num: str) -> PCGLookupResult:
    """Lookup numéro de compte PCG → libellé + classe + suggestions si pas trouvé.

    Tolérant aux variations : '401', '401 ', '0401', '401.0' tous renvoient '401'.
    Si pas trouvé exact, propose les sous-comptes du préfixe (ex: '4456' → 4456,
    44562, 44566, 44567).

    Args:
        num: Numéro de compte (str ou int castable).

    Returns:
        PCGLookupResult avec détail formaté pour injection LLM.
    """
    # Normalisation : strip leading zeros, strip espaces, drop décimales
    clean = str(num).strip().split(".")[0].lstrip("0") or "0"

    if clean in PCG_MAIN_ACCOUNTS:
        libelle = PCG_MAIN_ACCOUNTS[clean]
        classe_num = clean[0] if clean else "?"
        classe_lib = PCG_CLASSES.get(classe_num, "Classe inconnue")
        return {
            "found": True,
            "compte": clean,
            "libelle": libelle,
            "classe": classe_num,
            "classe_libelle": classe_lib,
            "detail": f"Compte {clean} = {libelle} (classe {classe_num} : {classe_lib})",
            "suggestions": [],
        }

    # Pas trouvé : propose sous-comptes du même préfixe (essais préfixe décroissant)
    suggestions: list[str] = []
    for prefix_len in range(len(clean) - 1, 0, -1):
        prefix = clean[:prefix_len]
        matches = sorted(
            [k for k in PCG_MAIN_ACCOUNTS if k.startswith(prefix) and k != clean]
        )
        if matches:
            suggestions = matches[:5]
            break

    classe_num = clean[0] if clean else "?"
    classe_lib = PCG_CLASSES.get(classe_num, "Classe inconnue")

    detail = f"Compte {clean} non trouvé dans le PCG principal."
    if classe_num in PCG_CLASSES:
        detail += f" Classe {classe_num} = {classe_lib}."
    if suggestions:
        detail += f" Comptes proches : {', '.join(suggestions)}."

    return {
        "found": False,
        "compte": clean,
        "libelle": "",
        "classe": classe_num,
        "classe_libelle": classe_lib,
        "detail": detail,
        "suggestions": suggestions,
    }


def verify_partie_double(ecritures: list[EcritureLine]) -> PartieDoubleResult:
    """Vérifie l'équilibre partie double : sum(debits) == sum(credits).

    Args:
        ecritures: Liste de lignes EcritureLine. Chaque ligne a debit OU credit
                   (pas les deux). Tolérance flottant 0.01€ (centimes).

    Returns:
        PartieDoubleResult avec détail formaté pour LLM.
    """
    if not ecritures:
        return {
            "valid": False,
            "sum_debits": 0.0,
            "sum_credits": 0.0,
            "diff": 0.0,
            "n_lines": 0,
            "detail": "Aucune écriture fournie. Une écriture comptable doit avoir au moins 2 lignes (1 débit + 1 crédit).",
        }

    sum_debits = sum(line.get("debit", 0) or 0 for line in ecritures)
    sum_credits = sum(line.get("credit", 0) or 0 for line in ecritures)
    diff = sum_debits - sum_credits
    n_lines = len(ecritures)

    # Tolérance 0.01€ pour les arrondis flottants
    valid = abs(diff) < 0.01

    if valid:
        detail = (
            f"✅ Écriture équilibrée : {sum_debits:.2f}€ au débit = {sum_credits:.2f}€ au crédit "
            f"({n_lines} lignes). La règle de la partie double est respectée."
        )
    else:
        sense = "supérieurs" if diff > 0 else "inférieurs"
        detail = (
            f"❌ Écriture déséquilibrée : débits ({sum_debits:.2f}€) {sense} aux crédits "
            f"({sum_credits:.2f}€). Différence : {abs(diff):.2f}€. "
            f"La règle de la partie double impose Σ débits = Σ crédits. "
            f"Vérifie tes montants ligne par ligne."
        )

    return {
        "valid": valid,
        "sum_debits": round(sum_debits, 2),
        "sum_credits": round(sum_credits, 2),
        "diff": round(diff, 2),
        "n_lines": n_lines,
        "detail": detail,
    }


def verify_calcul_tva(
    montant_ht: float,
    taux: float,
    actual_tva: float | None = None,
    actual_ttc: float | None = None,
) -> TVAVerifyResult:
    """Vérifie un calcul TVA standard.

    expected_tva = round(montant_ht * taux / 100, 2)
    expected_ttc = round(montant_ht + expected_tva, 2)

    Args:
        montant_ht: Montant HT en euros.
        taux: Taux TVA en pourcentage (5.5, 10, 20, 2.1, 0).
        actual_tva: Optionnel, montant TVA proposé par learner pour vérif.
        actual_ttc: Optionnel, montant TTC proposé par learner pour vérif.

    Returns:
        TVAVerifyResult avec détail formaté.
    """
    expected_tva = round(montant_ht * taux / 100, 2)
    expected_ttc = round(montant_ht + expected_tva, 2)

    taux_valide = taux in TVA_TAUX_STANDARD

    valid = True
    parts = []

    if not taux_valide:
        valid = False
        parts.append(
            f"⚠️ Taux {taux}% non standard FR — taux usuels : {TVA_TAUX_STANDARD} "
            f"(0=exonéré/exporté, 2.1=presse/médicaments remboursés, 5.5=alimentaire/livres, "
            f"10=intermédiaire restauration/transport, 20=normal)."
        )

    if actual_tva is not None:
        if abs(actual_tva - expected_tva) >= 0.01:
            valid = False
            parts.append(
                f"❌ TVA calculée incorrecte : {actual_tva:.2f}€ proposé vs {expected_tva:.2f}€ attendu "
                f"(HT {montant_ht}€ × {taux}% = {expected_tva}€)."
            )
        else:
            parts.append(f"✅ TVA correcte : {expected_tva:.2f}€ ({montant_ht}€ × {taux}%).")

    if actual_ttc is not None:
        if abs(actual_ttc - expected_ttc) >= 0.01:
            valid = False
            parts.append(
                f"❌ TTC calculé incorrect : {actual_ttc:.2f}€ proposé vs {expected_ttc:.2f}€ attendu "
                f"(HT + TVA = {montant_ht}€ + {expected_tva}€)."
            )
        else:
            parts.append(f"✅ TTC correct : {expected_ttc:.2f}€ ({montant_ht}€ HT + {expected_tva}€ TVA).")

    if not parts:
        # Pas de vérification spécifique demandée, juste calcul
        parts.append(
            f"Pour un montant HT de {montant_ht}€ et un taux TVA de {taux}% : "
            f"TVA = {expected_tva:.2f}€, TTC = {expected_ttc:.2f}€."
        )

    return {
        "valid": valid,
        "montant_ht": round(montant_ht, 2),
        "taux": taux,
        "expected_tva": expected_tva,
        "expected_ttc": expected_ttc,
        "actual_tva": round(actual_tva, 2) if actual_tva is not None else None,
        "actual_ttc": round(actual_ttc, 2) if actual_ttc is not None else None,
        "taux_valide": taux_valide,
        "detail": " ".join(parts),
    }


def verify_compte_classe(num: str, expected_classe: str) -> dict:
    """Vérifie qu'un compte appartient à une classe attendue.

    Args:
        num: Numéro de compte.
        expected_classe: Classe attendue ('1' à '9').

    Returns:
        dict avec valid + detail.
    """
    clean = str(num).strip().split(".")[0].lstrip("0") or "0"
    actual_classe = clean[0] if clean else "?"

    valid = actual_classe == str(expected_classe)
    classe_lib = PCG_CLASSES.get(actual_classe, "Classe inconnue")
    expected_lib = PCG_CLASSES.get(str(expected_classe), "Classe inconnue")

    if valid:
        detail = (
            f"✅ Compte {clean} appartient bien à la classe {expected_classe} "
            f"({classe_lib})."
        )
    else:
        detail = (
            f"❌ Compte {clean} appartient à la classe {actual_classe} ({classe_lib}), "
            f"mais tu attendais classe {expected_classe} ({expected_lib})."
        )

    return {
        "valid": valid,
        "compte": clean,
        "actual_classe": actual_classe,
        "expected_classe": str(expected_classe),
        "detail": detail,
    }


def lookup_studi_module(query: str) -> dict:
    """Phase 2 stub — mapping concept → module Studi BC1.X / BC2.X / BC3.X.

    Phase 1 : retourne mapping basique heuristique. Phase 2 : embedder + classifier
    sur programme Studi PDF + dropdown α anchor.

    Args:
        query: concept ou question Marie (ex: "TVA déductible", "rapprochement bancaire").

    Returns:
        dict avec module match + confidence.
    """
    q = query.lower()
    # Heuristique simple Phase 1
    mapping = [
        (["tva", "déductible", "collectée", "ca3", "ca12"], "BC1.4 / BC2.3", "TVA mécanisme + déclaration"),
        (["facture", "doit", "avoir"], "BC1.5", "Enregistrer factures"),
        (["bilan", "compte de résultat", "actif", "passif"], "BC1.2", "Compte de résultat + bilan"),
        (["écriture", "balance", "partie double"], "BC1.3", "Écritures + balance"),
        (["rapprochement", "bancaire"], "BC1.8", "Rapprochement bancaire + suivi tiers"),
        (["amortissement", "dépréciation"], "BC1.10 / BC1.12", "Amortissements + dépréciations"),
        (["paie", "bulletin", "salaire", "cotisation"], "BC2.1 / BC2.2", "Paie"),
        (["dsn", "déclaration sociale"], "BC2.1", "DSN paie"),
        (["rgpd", "archivage", "classement"], "BC3.2", "RGPD + archivage"),
        (["excel", "tableau de bord", "tcd", "reporting"], "BC3.4", "Reportings Excel"),
        (["sage", "ligne 100"], "BC1.18", "Sage Ligne 100"),
        (["facturation électronique", "ppf", "factur-x", "chorus"], "BC1.7", "Facturation électronique 2026"),
    ]
    for keywords, module, libelle in mapping:
        if any(k in q for k in keywords):
            return {
                "found": True,
                "module": module,
                "libelle": libelle,
                "confidence": "medium",
                "detail": f"La question semble relever de {module} — {libelle}.",
            }

    return {
        "found": False,
        "module": "?",
        "libelle": "",
        "confidence": "low",
        "detail": "Module Studi non identifié automatiquement. Marie peut préciser via le dropdown 'Module en cours'.",
    }
