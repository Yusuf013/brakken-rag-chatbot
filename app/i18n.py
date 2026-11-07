"""Talen: herkennen in welke taal een ouder schrijft, en vaste antwoorden per taal.

Laat de vertalingen controleren door iemand die de taal als moedertaal spreekt.
"""
import re

# code -> (naam voor het taalmodel, naam in de taal zelf)
LANGUAGES = {
    "nl": ("Dutch", "Nederlands"),
    "en": ("English", "English"),
    "tr": ("Turkish", "Türkçe"),
    "ar": ("Arabic", "العربية"),
    "pl": ("Polish", "Polski"),
    "uk": ("Ukrainian", "Українська"),
}

_STOPWORDS = {
    "nl": {"de", "het", "een", "is", "hoe", "wat", "wanneer", "mijn", "kind", "mag", "kan", "moet",
           "ik", "op", "van", "voor", "waar", "welke", "hoeveel", "school", "niet"},
    "en": {"the", "is", "are", "does", "do", "what", "when", "how", "can", "my", "child", "late",
           "time", "where", "which", "should", "will", "there", "much", "school"},
    "tr": {"ne", "nasıl", "zaman", "mi", "mı", "mu", "mü", "okul", "çocuğum", "benim", "için",
           "var", "kaç", "saat", "nerede", "hangi", "bir", "ve", "ile"},
    "pl": {"jak", "co", "kiedy", "czy", "moje", "mój", "dziecko", "szkoła", "szkoły", "jest", "się",
           "nie", "gdzie", "ile", "który", "na", "do", "w"},
}


def detect(question: str) -> str:
    """Eenvoudige taalherkenning zonder extra pakketten. Bij twijfel: Nederlands."""
    if re.search(r"[؀-ۿ]", question):
        return "ar"
    if re.search(r"[Ѐ-ӿ]", question):
        return "uk"
    if re.search(r"[ğışĞİŞ]", question):
        return "tr"
    if re.search(r"[ąęłńśźżĄĘŁŃŚŹŻ]", question):
        return "pl"
    words = set(re.findall(r"[\wçöüğış']+", question.lower()))
    scores = {lang: len(words & sw) for lang, sw in _STOPWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > scores["nl"] else "nl"


def resolve(question: str, language: str | None) -> str:
    """Gekozen taal gaat voor; 'auto' of onbekend = herkennen uit de vraag."""
    return language if language in LANGUAGES else detect(question)


def instruction(lang: str) -> str:
    name, native = LANGUAGES[lang]
    return f"Answer in {name} ({native}). Keep Dutch names of documents and systems such as Social Schools."


TEXTS = {
    "fallback": {
        "nl": "Dat kan ik helaas niet vinden in de informatie van de school. Neem voor deze vraag contact op met de school via {contact}.",
        "en": "Unfortunately I can't find that in the school's information. Please contact the school at {contact}.",
        "tr": "Maalesef bunu okulun bilgilerinde bulamıyorum. Bu soru için lütfen {contact} adresinden okulla iletişime geçin.",
        "ar": "للأسف لا أستطيع العثور على ذلك في معلومات المدرسة. يرجى التواصل مع المدرسة عبر {contact}.",
        "pl": "Niestety nie mogę znaleźć tej informacji w materiałach szkoły. W tej sprawie skontaktuj się ze szkołą: {contact}.",
        "uk": "На жаль, я не можу знайти цього в інформації школи. З цим питанням зверніться до школи: {contact}.",
    },
    "personal": {
        "nl": "Over individuele kinderen of medewerkers geef ik geen informatie. Neem hiervoor contact op met de leerkracht via Social Schools, of met de school via {contact}.",
        "en": "I can't give information about individual children or staff. Please contact the teacher via Social Schools, or the school at {contact}.",
        "tr": "Tek tek çocuklar veya personel hakkında bilgi veremem. Lütfen Social Schools üzerinden öğretmenle ya da {contact} adresinden okulla iletişime geçin.",
        "ar": "لا أستطيع تقديم معلومات عن أطفال أو موظفين بعينهم. يرجى التواصل مع المعلم عبر Social Schools، أو مع المدرسة عبر {contact}.",
        "pl": "Nie udzielam informacji o poszczególnych dzieciach ani pracownikach. Skontaktuj się z nauczycielem przez Social Schools lub ze szkołą: {contact}.",
        "uk": "Я не надаю інформації про окремих дітей чи працівників. Зверніться до вчителя через Social Schools або до школи: {contact}.",
    },
    "opvang": {
        "nl": "Ik help alleen met vragen over de basisschool. Voor vragen over de kinderopvang, peuterspeelgroep of BSO kijk je op de pagina Opvang: https://brakken.nl/opvang/",
        "en": "I only help with questions about the primary school. For questions about childcare, the toddler group or after-school care (BSO), see the Opvang page: https://brakken.nl/opvang/",
        "tr": "Sadece ilkokul ile ilgili sorulara yardımcı oluyorum. Kreş, oyun grubu veya okul sonrası bakım (BSO) ile ilgili sorular için Opvang sayfasına bakın: https://brakken.nl/opvang/",
        "ar": "أساعد فقط في الأسئلة المتعلقة بالمدرسة الابتدائية. للأسئلة حول رعاية الأطفال أو مجموعة ما قبل المدرسة أو الرعاية بعد المدرسة (BSO)، راجع صفحة Opvang: https://brakken.nl/opvang/",
        "pl": "Pomagam tylko w sprawach szkoły podstawowej. W sprawie opieki nad dziećmi, grupy przedszkolnej lub świetlicy pozaszkolnej (BSO) zajrzyj na stronę Opvang: https://brakken.nl/opvang/",
        "uk": "Я допомагаю лише з питаннями про початкову школу. Щодо догляду за дітьми, групи для малюків або позашкільного догляду (BSO) дивіться сторінку Opvang: https://brakken.nl/opvang/",
    },
}


def text(key: str, lang: str, **kwargs) -> str:
    return TEXTS[key].get(lang, TEXTS[key]["nl"]).format(**kwargs)
