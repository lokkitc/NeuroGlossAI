import time
from dataclasses import dataclass
from urllib.parse import quote
from urllib.parse import urlparse

import httpx

from app.core.config import settings


@dataclass(frozen=True)
class TopicRetrievalResult:
    query: str
    title: str | None
    url: str | None
    summary: str | None
    entities: list[str]
    roster: list[str]

    def to_prompt_block(self) -> str:
        parts: list[str] = []
        if self.title:
            parts.append(f"Title: {self.title}")
        if self.url:
            parts.append(f"URL: {self.url}")
        if self.summary:
            parts.append("Summary:\n" + self.summary)
        if self.entities:
            parts.append("Entities/related pages:\n- " + "\n- ".join(self.entities[: int(getattr(settings, 'TOPIC_RETRIEVAL_MAX_ENTITIES', 20) or 20)]))
        if self.roster:
            parts.append(
                "Verified roster (use ONLY these names if you mention characters/heroes; otherwise do NOT invent):\n- "
                + "\n- ".join(self.roster[: int(getattr(settings, 'TOPIC_RETRIEVAL_FANDOM_ROSTER_MAX', 80) or 80)])
            )
        return "\n\n".join(parts).strip()


_cache: dict[str, tuple[float, TopicRetrievalResult]] = {}


class TopicRetrievalService:
    async def retrieve(self, query: str) -> TopicRetrievalResult | None:
        if not getattr(settings, "TOPIC_RETRIEVAL_ENABLED", False):
            return None

        q = (query or "").strip()
        if not q:
            return None

        ttl = int(getattr(settings, "TOPIC_RETRIEVAL_CACHE_TTL_SECONDS", 86400) or 86400)
        now = time.time()
        cached = _cache.get(q)
        if cached is not None:
            ts, res = cached
            if (now - ts) <= ttl:
                return res

        timeout_s = float(getattr(settings, "TOPIC_RETRIEVAL_TIMEOUT_SECONDS", 8) or 8)
        lang = str(getattr(settings, "TOPIC_RETRIEVAL_WIKI_LANG", "ru") or "ru")

        res = await self._try_wikipedia(q, lang=lang, timeout_s=timeout_s)
        if res is None and lang != "en":
            res = await self._try_wikipedia(q, lang="en", timeout_s=timeout_s)

        if getattr(settings, "TOPIC_RETRIEVAL_FANDOM_ENABLED", False):
            try:
                fandom = await self._try_fandom(q, timeout_s=timeout_s)
            except Exception:
                fandom = None

            if res is None:
                res = fandom
            elif fandom is not None:
                merged_entities = list(dict.fromkeys([*(res.entities or []), *(fandom.entities or [])]))
                merged_roster = list(dict.fromkeys([*(getattr(res, "roster", None) or []), *(getattr(fandom, "roster", None) or [])]))
                res = TopicRetrievalResult(
                    query=res.query,
                    title=res.title,
                    url=res.url,
                    summary=res.summary,
                    entities=merged_entities,
                    roster=merged_roster,
                )

        if res is not None:
            _cache[q] = (now, res)
        return res

    async def _try_fandom(self, query: str, *, timeout_s: float) -> TopicRetrievalResult | None:
        max_results = int(getattr(settings, "TOPIC_RETRIEVAL_FANDOM_MAX_RESULTS", 5) or 5)
        base = "https://community.fandom.com"
        async with httpx.AsyncClient(timeout=timeout_s, follow_redirects=True) as client:
            opensearch = await client.get(
                f"{base}/api.php",
                params={
                    "action": "opensearch",
                    "search": query,
                    "limit": max_results,
                    "namespace": 0,
                    "format": "json",
                },
            )
            if opensearch.status_code != 200:
                return None

            data = opensearch.json()
            titles = data[1] if isinstance(data, list) and len(data) > 1 else []
            urls = data[3] if isinstance(data, list) and len(data) > 3 else []
            if not isinstance(titles, list) or not titles:
                return None

            entities: list[str] = []
            best_title = None
            best_url = None
            for i, t in enumerate(titles[:max_results]):
                if not isinstance(t, str) or not t.strip():
                    continue
                u = None
                if isinstance(urls, list) and i < len(urls) and isinstance(urls[i], str):
                    u = urls[i]
                if best_title is None:
                    best_title = t.strip()
                    best_url = u
                if u:
                    entities.append(f"{t.strip()} — {u}")
                else:
                    entities.append(t.strip())

            roster: list[str] = []
            summary = None
            # Try to enrich from the best result by calling the specific wiki MediaWiki API.
            if isinstance(best_url, str) and best_url.startswith("http"):
                try:
                    wiki_base = self._fandom_wiki_base(best_url)
                    if wiki_base:
                        summary = await self._fandom_page_intro(client, wiki_base, best_title or query)
                        roster = await self._fandom_try_roster(client, wiki_base, best_title or query)
                except Exception:
                    summary = None
                    roster = []

            return TopicRetrievalResult(
                query=query,
                title=best_title,
                url=best_url,
                summary=summary,
                entities=entities,
                roster=roster,
            )

    @staticmethod
    def _fandom_wiki_base(url: str) -> str | None:
        try:
            p = urlparse(url)
            if not p.scheme or not p.netloc:
                return None
            # Example: https://mobile-legends.fandom.com/wiki/...
            return f"{p.scheme}://{p.netloc}".rstrip("/")
        except Exception:
            return None

    async def _fandom_page_intro(self, client: httpx.AsyncClient, wiki_base: str, title_or_query: str) -> str | None:
        # Use MediaWiki extracts for an intro summary.
        resp = await client.get(
            f"{wiki_base}/api.php",
            params={
                "action": "query",
                "format": "json",
                "prop": "extracts",
                "exintro": 1,
                "explaintext": 1,
                "redirects": 1,
                "titles": title_or_query,
            },
        )
        if resp.status_code != 200:
            return None
        j = resp.json()
        pages = ((j.get("query") or {}).get("pages") or {}) if isinstance(j, dict) else {}
        for _, page in (pages.items() if isinstance(pages, dict) else []):
            ex = page.get("extract") if isinstance(page, dict) else None
            if isinstance(ex, str) and ex.strip():
                return ex.strip()[:2000]
        return None

    async def _fandom_try_roster(self, client: httpx.AsyncClient, wiki_base: str, title_or_query: str) -> list[str]:
        max_roster = int(getattr(settings, "TOPIC_RETRIEVAL_FANDOM_ROSTER_MAX", 80) or 80)

        # 1) Read categories of the best-matching page.
        cat_resp = await client.get(
            f"{wiki_base}/api.php",
            params={
                "action": "query",
                "format": "json",
                "prop": "categories",
                "cllimit": 50,
                "redirects": 1,
                "titles": title_or_query,
            },
        )
        cats: list[str] = []
        if cat_resp.status_code == 200:
            cj = cat_resp.json()
            pages = ((cj.get("query") or {}).get("pages") or {}) if isinstance(cj, dict) else {}
            for _, page in (pages.items() if isinstance(pages, dict) else []):
                categories = page.get("categories") if isinstance(page, dict) else None
                if isinstance(categories, list):
                    for c in categories:
                        t = c.get("title") if isinstance(c, dict) else None
                        if isinstance(t, str) and t.startswith("Category:"):
                            cats.append(t[len("Category:") :].strip())

        # 2) Pick likely roster categories.
        keywords = [
            "character",
            "characters",
            "hero",
            "heroes",
            "champion",
            "champions",
            "playable",
            "units",
            "agents",
        ]
        # Add RU variants too; many wikis are EN but some use RU.
        keywords += ["персона", "персонажи", "герои", "герой", "чемпион", "чемпионы"]

        likely = []
        for c in cats:
            low = c.lower()
            if any(k in low for k in keywords):
                likely.append(c)

        # Fallback common category names.
        if not likely:
            likely = ["Characters", "Heroes", "Playable characters", "Champions"]

        roster: list[str] = []
        for cat_name in likely:
            roster.extend(await self._fandom_category_members(client, wiki_base, cat_name, limit=max_roster))
            # Stop early once we have enough.
            roster = list(dict.fromkeys([r for r in roster if isinstance(r, str) and r.strip()]))
            if len(roster) >= max_roster:
                break

        return roster[:max_roster]

    async def _fandom_category_members(self, client: httpx.AsyncClient, wiki_base: str, category: str, *, limit: int) -> list[str]:
        out: list[str] = []
        cmcontinue = None
        # Keep requests bounded; we only need a small roster.
        per_page = min(50, max(10, limit))

        for _ in range(0, 5):
            params = {
                "action": "query",
                "format": "json",
                "list": "categorymembers",
                "cmtitle": f"Category:{category}",
                "cmlimit": per_page,
                "cmnamespace": 0,
            }
            if cmcontinue:
                params["cmcontinue"] = cmcontinue

            resp = await client.get(f"{wiki_base}/api.php", params=params)
            if resp.status_code != 200:
                break

            j = resp.json()
            members = ((j.get("query") or {}).get("categorymembers") or []) if isinstance(j, dict) else []
            if isinstance(members, list):
                for it in members:
                    title = it.get("title") if isinstance(it, dict) else None
                    if isinstance(title, str) and title.strip():
                        out.append(title.strip())
                        if len(out) >= limit:
                            return out[:limit]

            cont = (j.get("continue") or {}).get("cmcontinue") if isinstance(j, dict) else None
            if not isinstance(cont, str) or not cont.strip():
                break
            cmcontinue = cont

        return out[:limit]

    async def _try_wikipedia(self, query: str, *, lang: str, timeout_s: float) -> TopicRetrievalResult | None:
        base = f"https://{lang}.wikipedia.org"
        async with httpx.AsyncClient(timeout=timeout_s, follow_redirects=True) as client:
            try:
                # 1) Search for best title
                opensearch = await client.get(
                    f"{base}/w/api.php",
                    params={
                        "action": "opensearch",
                        "search": query,
                        "limit": 1,
                        "namespace": 0,
                        "format": "json",
                    },
                )
                if opensearch.status_code != 200:
                    return None
                data = opensearch.json()
                titles = data[1] if isinstance(data, list) and len(data) > 1 else []
                urls = data[3] if isinstance(data, list) and len(data) > 3 else []
                title = titles[0] if isinstance(titles, list) and titles else None
                url = urls[0] if isinstance(urls, list) and urls else None
                if not isinstance(title, str) or not title.strip():
                    return None

                # 2) Summary
                title_encoded = quote(title.replace(" ", "_"), safe="")
                summary_resp = await client.get(f"{base}/api/rest_v1/page/summary/{title_encoded}")
                summary = None
                if summary_resp.status_code == 200:
                    j = summary_resp.json()
                    summary = j.get("extract") if isinstance(j, dict) else None

                # 3) Related links as entities
                entities: list[str] = []
                links_resp = await client.get(
                    f"{base}/w/api.php",
                    params={
                        "action": "query",
                        "format": "json",
                        "prop": "links",
                        "titles": title,
                        "plnamespace": 0,
                        "pllimit": int(getattr(settings, "TOPIC_RETRIEVAL_MAX_ENTITIES", 20) or 20),
                    },
                )
                if links_resp.status_code == 200:
                    lj = links_resp.json()
                    pages = ((lj.get("query") or {}).get("pages") or {}) if isinstance(lj, dict) else {}
                    for _, page in (pages.items() if isinstance(pages, dict) else []):
                        links = page.get("links") if isinstance(page, dict) else None
                        if isinstance(links, list):
                            for it in links:
                                t = it.get("title") if isinstance(it, dict) else None
                                if isinstance(t, str) and t.strip():
                                    entities.append(t.strip())

                return TopicRetrievalResult(
                    query=query,
                    title=title,
                    url=url,
                    summary=summary if isinstance(summary, str) and summary.strip() else None,
                    entities=entities,
                    roster=[],
                )
            except Exception:
                return None
