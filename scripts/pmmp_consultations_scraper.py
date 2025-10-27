"""
Scraper ciblé PMMP (consultations) – httpx + BeautifulSoup

Fonctionnement:
- Ouvre la recherche avancée (version desktop), remplit la date, soumet le formulaire
- Récupère TOUS les liens de détail de consultation via href (même si <a> contient juste un <img>)
- Va sur chaque page détail et extrait le bloc #recap-consultation
- Ecrit un JSONL (une ligne par consultation) avec un id stable

Usage (PowerShell):
	python scripts/pmmp_consultations_scraper.py 27/04/2025

Sortie:
- Fichier consultations.jsonl à la racine du projet
- Logs HTML dans logs/ pour debug (page liste)
"""

import asyncio
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from urllib.parse import parse_qs, urlencode, urljoin, urlparse


BASE_URL = "https://www.marchespublics.gov.ma"
# Page de recherche (desktop)
SEARCH_PATH = "/index.php?page=entreprise.EntrepriseAdvancedSearch&searchAnnCons&mobile=out"

# Champs WebForms spécifiques vus sur la page de recherche
DATE_FIELD_NAME = "ctl0$CONTENU_PAGE$AdvancedSearch$dateMiseEnLigneCalculeStart"
SUBMIT_FIELD_NAME = "ctl0$CONTENU_PAGE$AdvancedSearch$lancerRecherche"
SUBMIT_FIELD_VALUE = "Lancer la recherche"

OUTPUT_FILE = Path("consultations.jsonl")


# -------- utilitaires bas niveau --------

async def polite_get(client: httpx.AsyncClient, url: str, **kwargs) -> httpx.Response:
	"""GET avec un petit délai pour rester policé."""
	await asyncio.sleep(1.0)
	resp = await client.get(url, **kwargs)
	resp.raise_for_status()
	return resp


async def polite_post(client: httpx.AsyncClient, url: str, **kwargs) -> httpx.Response:
	await asyncio.sleep(1.0)
	resp = await client.post(url, **kwargs)
	resp.raise_for_status()
	return resp


def extract_hidden_fields(form_soup: BeautifulSoup) -> dict:
	"""
	Récupère tous les <input> du formulaire (hidden, text...) pour reconstruire le POST.
	On réécrasera ensuite les champs qu'on veut forcer (date + bouton).
	"""
	data: dict[str, str] = {}
	for inp in form_soup.find_all("input"):
		name = inp.get("name")
		if not name:
			continue
		value = inp.get("value", "")
		data[name] = value
	return data


def parse_consultation_links(list_html: str, base_url: str) -> list[str]:
	"""
	IMPORTANT: Ici on ne regarde PAS le texte du lien. On regarde juste le href.
	On veut tous les <a href="...EntrepriseDetailConsultation&refConsultation=...">
	même si l'intérieur du <a> est juste <img>.
	"""
	soup = BeautifulSoup(list_html, "lxml")
	urls: list[str] = []
	for a in soup.find_all("a", href=True):
		href = a["href"]
		# Accepte les deux variantes observées: Detail vs Details
		if (
			"EntrepriseDetailsConsultation" in href
			or "EntrepriseDetailConsultation" in href
		):
			abs_url = urljoin(base_url, href)
			# Canonicaliser: ne garder que refConsultation & orgAcronyme pour déduplication
			try:
				p = urlparse(abs_url)
				qs = parse_qs(p.query)
				ref = qs.get("refConsultation", [None])[0]
				org = qs.get("orgAcronyme", [None])[0]
				if ref and org:
					q = urlencode({"page": p.path.split("page=")[-1] if "page=" in p.path else "entreprise.EntrepriseDetailsConsultation", "refConsultation": ref, "orgAcronyme": org})
					abs_url = urljoin(base_url, f"/index.php?page=entreprise.EntrepriseDetailsConsultation&refConsultation={ref}&orgAcronyme={org}")
			except Exception:
				pass
			urls.append(abs_url)

	# déduplication en gardant l'ordre
	seen: set[str] = set()
	deduped: list[str] = []
	for u in urls:
		key = u.split("#")[0]
		if key not in seen:
			seen.add(key)
			deduped.append(u)
	return deduped


def text_or_none(scope_soup: BeautifulSoup, css_selector: str) -> Optional[str]:
	el = scope_soup.select_one(css_selector)
	if el:
		# normalisation espaces / sauts de ligne
		return " ".join(el.get_text(strip=True).split())
	return None


def parse_consultation_detail(detail_html: str) -> dict:
	"""
	Extrait les infos essentielles depuis #recap-consultation.
	On mappe directement vers les champs métier importants.
	"""
	soup = BeautifulSoup(detail_html, "lxml")
	bloc = soup.select_one("#recap-consultation")
	if bloc is None:
		return {}

	data: dict[str, Optional[str]] = {}
	data["date_limite"] = text_or_none(
		bloc,
		"#ctl0_CONTENU_PAGE_idEntrepriseConsultationSummary_dateHeureLimiteRemisePlis",
	)
	data["ref"] = text_or_none(
		bloc,
		"#ctl0_CONTENU_PAGE_idEntrepriseConsultationSummary_reference",
	)
	data["objet"] = text_or_none(
		bloc,
		"#ctl0_CONTENU_PAGE_idEntrepriseConsultationSummary_objet",
	)
	data["entite_publique"] = text_or_none(
		bloc,
		"#ctl0_CONTENU_PAGE_idEntrepriseConsultationSummary_entiteAchat",
	)

	# Procédure = type + mode
	proc = text_or_none(
		bloc,
		"#ctl0_CONTENU_PAGE_idEntrepriseConsultationSummary_typeProcedure",
	)
	mode = text_or_none(
		bloc,
		"#ctl0_CONTENU_PAGE_idEntrepriseConsultationSummary_modePassation",
	)
	data["type_procedure"] = (proc or "") + ((" " + mode) if mode else "")

	data["categorie"] = text_or_none(
		bloc,
		"#ctl0_CONTENU_PAGE_idEntrepriseConsultationSummary_categoriePrincipale",
	)
	data["lieu_execution"] = text_or_none(
		bloc,
		"#ctl0_CONTENU_PAGE_idEntrepriseConsultationSummary_lieuxExecutions",
	)
	data["estimation_ttc"] = text_or_none(
		bloc,
		"#ctl0_CONTENU_PAGE_idEntrepriseConsultationSummary_idReferentielZoneText_RepeaterReferentielZoneText_ctl0_labelReferentielZoneText",
	)
	data["caution_provisoire"] = text_or_none(
		bloc,
		"#ctl0_CONTENU_PAGE_idEntrepriseConsultationSummary_cautionProvisoire",
	)
	data["lieu_ouverture_plis"] = text_or_none(
		bloc,
		"#ctl0_CONTENU_PAGE_idEntrepriseConsultationSummary_lieuOuverturePlis",
	)
	data["adresse_retrait_dossiers"] = text_or_none(
		bloc,
		"#ctl0_CONTENU_PAGE_idEntrepriseConsultationSummary_adresseRetraitDossiers",
	)
	data["adresse_depot_offres"] = text_or_none(
		bloc,
		"#ctl0_CONTENU_PAGE_idEntrepriseConsultationSummary_adresseDepotOffres",
	)
	data["variante_autorisee"] = text_or_none(
		bloc,
		"#ctl0_CONTENU_PAGE_idEntrepriseConsultationSummary_varianteValeur",
	)

	# Visites des lieux (liste <li>)
	visites_block = bloc.select_one(
		"#ctl0_CONTENU_PAGE_idEntrepriseConsultationSummary_panelRepeaterVisitesLieux"
	)
	if visites_block:
		visites_txt = " ".join(visites_block.get_text(" ", strip=True).split())
	else:
		visites_txt = None
	data["visites_lieux"] = visites_txt

	return data


def compute_uid(entite: Optional[str], ref: Optional[str], date_limite: Optional[str]) -> str:
	"""ID unique stable = sha256(entité|ref|date_limite)."""
	base = f"{entite or ''}|{ref or ''}|{date_limite or ''}"
	return hashlib.sha256(base.encode("utf-8")).hexdigest()


def append_jsonl(path: Path, record: dict) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	with path.open("a", encoding="utf-8") as f:
		f.write(json.dumps(record, ensure_ascii=False) + "\n")


# -------- pipeline principal --------


async def run_scraper(date_recherche: str = "27/04/2025") -> None:
	"""
	1. GET la page de recherche
	2. Remplit la date
	3. POST 'Lancer la recherche'
	4. Récupère les liens détail de TOUTES les consultations (icônes <img>)
	5. Va sur chaque détail, extrait les données, calcule un ID, écrit en JSONL
	"""

	async with httpx.AsyncClient(
		base_url=BASE_URL,
		follow_redirects=True,
		headers={
			# User-Agent propre pour rester poli et traçable
			"User-Agent": "PMMP-scraper-research/0.1 (+contact:your-email@example.com)",
			"Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
			"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
		},
		timeout=30.0,
	) as client:
		# 1. Page de recherche (forcer la version desktop)
		search_resp = await polite_get(client, SEARCH_PATH)
		soup = BeautifulSoup(search_resp.text, "lxml")
		form = soup.find("form")
		if form is None:
			raise RuntimeError("Formulaire introuvable sur la page de recherche.")

		action = form.get("action") or SEARCH_PATH
		# Si on est redirigé vers la version mobile, revenir à la version complète
		if action.startswith("/mobile/"):
			action = action.replace("/mobile/", "/")
			if "mobile=out" not in action:
				sep = "&" if "?" in action else "?"
				action = f"{action}{sep}mobile=out"
		method = (form.get("method") or "post").lower()

		# 2. On récupère TOUS les champs (<input>) du form
		payload = extract_hidden_fields(form)

		# 3. On force notre date (plusieurs tentatives de nommage)
		payload[DATE_FIELD_NAME] = date_recherche
		# Autres variantes possibles rencontrées
		for key in list(payload.keys()):
			lk = key.lower()
			if (
				"advancedsearch" in lk
				and ("datemiseenligne" in lk or "datepublication" in lk)
				and ("start" in lk or "debut" in lk or "du" in lk)
			):
				payload[key] = date_recherche

		# 4. Simuler le clic sur 'Lancer la recherche'
		payload[SUBMIT_FIELD_NAME] = SUBMIT_FIELD_VALUE

		# 5. Soumission du formulaire -> liste résultats
		if method == "post":
			# Ajouter un Referer pour ressembler à un vrai post
			headers = {"Referer": urljoin(BASE_URL, SEARCH_PATH)}
			list_resp = await polite_post(client, action, data=payload, headers=headers)
		else:
			list_resp = await polite_get(client, action, params=payload)

		list_html = list_resp.text
		# Debug: sauvegarder la page liste
		try:
			logs = Path("logs"); logs.mkdir(exist_ok=True)
			(logs / "consultations_list.html").write_text(list_html, encoding="utf-8")
		except Exception:
			pass

		# 6. Extraire tous les liens détail consultation à partir des <a><img></a>
		detail_urls = parse_consultation_links(list_html, BASE_URL)

		# Fallback: si aucun lien trouvé, charger la page des consultations en cours
		if not detail_urls:
			fallback_path = "/index.php?page=entreprise.EntrepriseAdvancedSearch&AllCons&EnCours&searchAnnCons&mobile=out"
			print("[INFO] Aucun lien après POST. Fallback vers la liste 'En cours'...")
			fb_resp = await polite_get(client, fallback_path)
			fb_html = fb_resp.text
			try:
				logs = Path("logs"); logs.mkdir(exist_ok=True)
				(logs / "consultations_list_fallback.html").write_text(fb_html, encoding="utf-8")
			except Exception:
				pass
			detail_urls = parse_consultation_links(fb_html, BASE_URL)

		print(f"[INFO] Liens détail trouvés: {len(detail_urls)}")

		# (Optionnel) vider le fichier de sortie si tu veux fresh run
		if OUTPUT_FILE.exists():
			OUTPUT_FILE.unlink()
		OUTPUT_FILE.touch()

		# 7. Pour chaque consultation trouvée
		for detail_url in detail_urls:
			detail_resp = await polite_get(client, detail_url)
			data = parse_consultation_detail(detail_resp.text)

			# Ajouter les paramètres refConsultation / orgAcronyme (utile pour debug)
			parsed = urlparse(detail_url)
			qs = parse_qs(parsed.query)
			data["refConsultation"] = qs.get("refConsultation", [None])[0]
			data["orgAcronyme"] = qs.get("orgAcronyme", [None])[0]

			# ID unique stable
			data["id"] = compute_uid(
				data.get("entite_publique"),
				data.get("ref"),
				data.get("date_limite"),
			)

			# horodatage de collecte (ISO, UTC)
			try:
				from datetime import UTC
				data["scraped_at"] = datetime.now(UTC).isoformat(timespec="seconds")
			except Exception:
				# Fallback pour versions Python anciennes
				data["scraped_at"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"

			# Sauvegarde JSONL (une ligne par consultation)
			append_jsonl(OUTPUT_FILE, data)

			# Affichage debug console
			print(f"[OK] {data.get('ref')} ({data.get('id')})")


def _parse_cli_date_arg() -> Optional[str]:
	"""Permet de passer une date en argument simple (DD/MM/YYYY)."""
	import sys

	if len(sys.argv) >= 2:
		return sys.argv[1]
	return None


if __name__ == "__main__":
	# Date par défaut ou via arg CLI
	arg_date = _parse_cli_date_arg() or "27/04/2025"
	asyncio.run(run_scraper(arg_date))

