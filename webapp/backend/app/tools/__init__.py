"""S57 — Backend tools for AccountingDomain (Maître Comptable Phase 1).

Tools fonctionnels appelés par le chatflow Dify via tool calling :
- lookup_pcg_account : numéro PCG → libellé + classe
- verify_partie_double : check sum débit = sum crédit
- verify_calcul_tva : check calcul TVA HT/TTC/taux
- verify_compte_classe : numéro → classe (1-7)
- lookup_studi_module : recherche concept dans programme Studi

Pattern réutilisable Phase 2+ pour autres domaines fermés (PyMentor unit
tests, CyberMentor rules-based).
"""
