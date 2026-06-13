from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FactCheckSource:
    name: str
    url: str
    region: str
    reliability: int
    tags: tuple[str, ...]
    feed_url: str | None = None


FACT_CHECK_SOURCES: list[FactCheckSource] = [
    FactCheckSource("Alt News", "https://www.altnews.in/", "India", 88, ("politics", "viral", "media"), "https://www.altnews.in/feed/"),
    FactCheckSource("PIB Fact Check", "https://www.pib.gov.in/factcheck.aspx", "India", 96, ("government", "policy"), None),
    FactCheckSource("Factly", "https://factly.in/", "India", 88, ("data", "policy", "viral"), "https://factly.in/feed/"),
    FactCheckSource("BOOM Live Fact Check", "https://www.boomlive.in/fact-check", "India", 88, ("viral", "social"), "https://www.boomlive.in/rss/fact-check"),
    FactCheckSource("The Quint WebQoof", "https://www.thequint.com/news/webqoof", "India", 84, ("viral", "media"), "https://www.thequint.com/news/webqoof.rss"),
    FactCheckSource("India Today Fact Check", "https://www.indiatoday.in/fact-check", "India", 83, ("news", "viral"), "https://www.indiatoday.in/rss/1206578"),
    FactCheckSource("NewsChecker", "https://newschecker.in/", "India", 86, ("viral", "regional"), "https://newschecker.in/feed/"),
    FactCheckSource("Vishvas News", "https://www.vishvasnews.com/", "India", 84, ("regional", "viral"), "https://www.vishvasnews.com/feed/"),
    FactCheckSource("AFP Fact Check India", "https://factcheck.afp.com/", "India", 92, ("global", "media"), "https://factcheck.afp.com/rss.xml"),
    FactCheckSource("DFRAC", "https://dfrac.org/", "India", 78, ("digital", "forensics"), "https://dfrac.org/en/feed/"),
    FactCheckSource("Google Fact Check Explorer", "https://toolbox.google.com/factcheck/explorer", "Global", 90, ("index", "search"), None),
    FactCheckSource("Snopes", "https://www.snopes.com/", "Global", 87, ("viral", "internet"), "https://www.snopes.com/feed/"),
    FactCheckSource("PolitiFact", "https://www.politifact.com/", "Global", 88, ("politics", "public claims"), "https://www.politifact.com/rss/factchecks/"),
    FactCheckSource("FactCheck.org", "https://www.factcheck.org/", "Global", 88, ("politics", "public claims"), "https://www.factcheck.org/feed/"),
    FactCheckSource("Reuters Fact Check", "https://www.reuters.com/fact-check/", "Global", 93, ("news", "global"), None),
    FactCheckSource("AP Fact Check", "https://apnews.com/hub/ap-fact-check", "Global", 93, ("news", "global"), "https://apnews.com/hub/ap-fact-check?output=rss"),
    FactCheckSource("Full Fact", "https://fullfact.org/", "Global", 88, ("uk", "policy"), "https://fullfact.org/feed/"),
    FactCheckSource("Lead Stories", "https://leadstories.com/", "Global", 86, ("viral", "social"), "https://leadstories.com/feeds/rss.xml"),
    FactCheckSource("Washington Post Fact Checker", "https://www.washingtonpost.com/news/fact-checker/", "Global", 82, ("politics", "analysis"), None),
    FactCheckSource("Poynter IFCN", "https://www.poynter.org/ifcn/", "Global", 91, ("standards", "network"), "https://www.poynter.org/ifcn/feed/"),
]


def trusted_sources_by_region(region: str) -> list[FactCheckSource]:
    region = region.lower()
    primary = [src for src in FACT_CHECK_SOURCES if src.region.lower() == region]
    global_sources = [src for src in FACT_CHECK_SOURCES if src.region == "Global"]
    chosen = primary + global_sources
    return sorted(chosen, key=lambda source: source.reliability, reverse=True)[:10]
