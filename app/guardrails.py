"""Harde regels die vóór het taalmodel worden gecontroleerd.

Een prompt is een verzoek aan het model; deze regels werken altijd, wat het model ook doet.
Ze vangen de gevallen af waar een fout antwoord echt schade doet: persoonlijke informatie
en vragen over de kinderopvang (andere organisatie, andere regels).

De trefwoorden dekken Nederlands, Engels, Turks, Pools, Arabisch en Oekraïens, maar niet
elke formulering. De regels in de prompt zijn het tweede vangnet.
"""
import re

from app import config, i18n

# Overblijven heet op de site ook "tussenschoolse opvang", maar hoort wél bij de school.
_SCHOOL_OPVANG = re.compile(r"overblijv|tussenschools|\btso\b|lunch", re.I)

_OPVANG = re.compile(
    r"\b(bso|kdv|psg|kinderopvang|kinderdagverblijf|peuterspeelgroep|peuteropvang|"
    r"buitenschoolse|naschoolse opvang|voorschoolse|opvang|harlekijn|"
    r"daycare|childcare|after.?school care|"           # en
    r"kreş|kres|çocuk bakım|"                          # tr
    r"żłobek|zlobek|świetlica|swietlica|"              # pl
    r"حضانة|"                                          # ar
    r"ясла|садок|продовжений день)\b",                 # uk
    re.I,
)

# Een persoon (leerkracht, kind) gecombineerd met contactgegevens of persoonlijke resultaten
_PERSON = re.compile(
    r"\b(juf|juffrouw|meester|leerkracht|docent|leraar|lerares|directeur|intern begeleider|ib'?er|"
    r"mijn (zoon|dochter|kind)|ons kind|"
    r"teacher|my (son|daughter|child)|"
    r"öğretmen\w*|ogretmen\w*|oğlum|kızım|çocuğum|"
    r"nauczyciel\w*|mojego (syna|dziecka)|mojej córki|"
    r"معلم\w*|المعلم\w*|ابني|ابنتي|"
    r"вчител\w*|мого сина|моєї доньки|моєї дитини)",
    re.I,
)
_PERSONAL_DATA = re.compile(
    r"\b(telefoon\w*|nummer|06|adres|e-?mail\w*|mail|whatsapp|privé|prive|woont|"
    r"cijfer\w*|toets\w*|rapport|resultat\w*|gedrag|dossier|"
    r"phone|number|address|grades?|scores?|behaviou?r|"
    r"telefon\w*|numara\w*|adres\w*|karne\w*|sınav\w*|"
    r"numer\w*|ocen\w*|sprawdzian\w*|"
    r"هاتف|رقم|عنوان|درجات|"
    r"телефон\w*|номер\w*|адрес\w*|оцінк\w*)",
    re.I,
)


def check(question: str, lang: str = "nl") -> str | None:
    """Geeft een vast antwoord terug als de vraag onder een harde regel valt, anders None."""
    if _PERSON.search(question) and _PERSONAL_DATA.search(question):
        return i18n.text("personal", lang, contact=config.SCHOOL_CONTACT)
    if _OPVANG.search(question) and not _SCHOOL_OPVANG.search(question):
        return i18n.text("opvang", lang)
    return None
