from pysblgnt import morphgnt_rows
import xml.etree.ElementTree as ET
import json
import os
import unicodedata


# Canonical list of New Testament books in order
NEW_TESTAMENT = [
    (1, "Matthew",    "Mt", "The Gospel According to Matthew", "Matt"),
    (2, "Mark",       "Mk", "The Gospel According to Mark", "Mark"),
    (3, "Luke",       "Lk", "The Gospel According to Luke", "Luke"),
    (4, "John",       "Jn", "The Gospel According to John", "John"),
    (5, "Acts",      "Acts", "The Acts of the Apostles", "Acts"),
    (6, "Romans",    "Rom", "The Letter to the Romans", "Rom"),
    (7, "1 Corinthians", "1Co", "The First Letter to the Corinthians", "1Cor"),
    (8, "2 Corinthians", "2Co", "The Second Letter to the Corinthians", "2Cor"),
    (9, "Galatians",  "Gal", "The Letter to the Galatians", "Gal"),
    (10, "Ephesians",  "Eph", "The Letter to the Ephesians", "Eph"),
    (11, "Philippians", "Phil", "The Letter to the Philippians", "Phil"),
    (12, "Colossians", "Col", "The Letter to the Colossians", "Col"),
    (13, "1 Thessalonians", "1Th", "The First Letter to the Thessalonians", "1Thess"),
    (14, "2 Thessalonians", "2Th", "The Second Letter to the Thessalonians", "2Thess"),
    (15, "1 Timothy",  "1Ti", "The First Letter to Timothy", "1Tim"),
    (16, "2 Timothy",  "2Ti", "The Second Letter to Timothy", "2Tim"),
    (17, "Titus",      "Tit", "The Letter to Titus", "Titus"),
    (18, "Philemon",   "Phm", "The Letter to Philemon", "Philem"),
    (19, "Hebrews",    "Heb", "The Letter to the Hebrews", "Heb"),
    (20, "James",      "Jas", "The Letter of James", "Jas"),
    (21, "1 Peter",    "1Pe", "The First Letter of Peter", "1Pet"),
    (22, "2 Peter",    "2Pe", "The Second Letter of Peter", "2Pet"),
    (23, "1 John",     "1Jn", "The First Letter of John", "1John"),
    (24, "2 John",     "2Jn", "The Second Letter of John", "2John"),
    (25, "3 John",     "3Jn", "The Third Letter of John", "3John"),
    (26, "Jude",      "Jude", "The Letter of Jude", "Jude"),
    (27, "Revelation", "Rev", "The Revelation to John", "Rev"),
]

# Create lookup dictionaries
SHORT_NAME_TO_DATA = {book[1]: (book[0], book[2], book[4]) for book in NEW_TESTAMENT}
NUMBER_TO_DATA = {book[0]: (book[1], book[2], book[4]) for book in NEW_TESTAMENT}
ABBREV_TO_DATA = {book[2]: (book[0], book[1], book[4]) for book in NEW_TESTAMENT}
KJV_ABBREV_TO_DATA = {book[4]: (book[0], book[1], book[2]) for book in NEW_TESTAMENT}

def get_book_data(identifier):
    """Get book data by short name, number, abbreviation, or KJV abbreviation"""
    if isinstance(identifier, int):
        return NUMBER_TO_DATA.get(identifier)
    if identifier in SHORT_NAME_TO_DATA:
        return SHORT_NAME_TO_DATA[identifier]
    if identifier in ABBREV_TO_DATA:
        return ABBREV_TO_DATA[identifier]
    if identifier in KJV_ABBREV_TO_DATA:
        return KJV_ABBREV_TO_DATA[identifier]
    return None


def get_full_text_with_asterisk(element):
    """Recursively get all text from an element, replacing subelements with an asterisk."""
    parts = []
    if element.text:
        parts.append(element.text)
    for child in element:
        parts.append("*")  # Insert asterisk for subelement
        if child.tail:
            parts.append(child.tail)
    return ''.join(parts).strip()

def parse_strongs_greek(xml_file):
    """Parse the strongsgreek.xml file and build a lookup dictionary with multiple fields per entry."""
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Create a dictionary for lookups
    unicode_to_entry = {}

    # Iterate over all <entry> elements
    for entry in root.findall("entries/entry"):
        # Get the unicode value from the greek subelement
        greek = entry.find("greek")
        if greek is not None:
            unicode_value = greek.get("unicode")  
            if unicode_value:
                pronunciation = entry.find("pronunciation")
                strongs_def = entry.find("strongs_def")
                translit = greek.get("translit") if greek.get("translit") else None

                # Use the new function to get the full text with asterisks
                definition = get_full_text_with_asterisk(strongs_def) if strongs_def is not None else None

                entry_dict = {
                    'definition': definition,
                    'pronunciation': pronunciation.get('strongs') if pronunciation is not None and pronunciation.get('strongs') else None,
                    'transliteration': translit
                }
                unicode_to_entry[unicodedata.normalize("NFC",unicode_value)] = entry_dict

    return unicode_to_entry

def lookup_entry_by_unicode(unicode_value, lookup_dict):
    """Look up an entry by its Unicode value and return the entry dict or None."""
    return lookup_dict.get(unicodedata.normalize("NFC",unicode_value), None)

      

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def interpret_ccat_pos(ccat_pos):
    """
    Interpret the CCAT part of speech (ccat-pos) key.
    
    Args:
        ccat_pos (str): The CCAT part of speech key (two characters).
    
    Returns:
        str: The description of the part of speech.
    """
    pos_map = {
        "A-": "Adjective",
        "C-": "Conjunction",
        "D-": "Adverb",
        "I-": "Interjection",
        "N-": "Noun",
        "P-": "Preposition",
        "RA": "Definite Article",
        "RD": "Demonstrative Pronoun",
        "RI": "Interrogative/Indefinite Pronoun",
        "RP": "Personal Pronoun",
        "RR": "Relative Pronoun",
        "V-": "Verb",
        "X-": "Particle",
    }
    return pos_map.get(ccat_pos, "Unknown Part of Speech")


def interpret_ccat_parse(ccat_parse):
    """
    Interpret the CCAT parsing (ccat-parse) key.

    Args:
        ccat_parse (str): The CCAT parsing key.

    Returns:
        str: A human-readable description of the grammatical information.
    """
    parse_map = [
        ('Person', {'1': '1st person', '2': '2nd person', '3': '3rd person'}),
        ('Tense', {'P': 'present', 'I': 'imperfect', 'F': 'future', 'A': 'aorist', 'X': 'perfect', 'Y': 'pluperfect'}),
        ('Voice', {'A': 'active', 'M': 'middle', 'P': 'passive'}),
        ('Mood', {'I': 'indicative', 'D': 'imperative', 'S': 'subjunctive', 'O': 'optative', 'N': 'infinitive', 'P': 'participle'}),
        ('Case', {'N': 'nominative', 'G': 'genitive', 'D': 'dative', 'A': 'accusative'}),
        ('Number', {'S': 'singular', 'P': 'plural'}),
        ('Gender', {'M': 'masculine', 'F': 'feminine', 'N': 'neuter'}),
        ('Degree', {'C': 'comparative', 'S': 'superlative'}),
    ]

    result = []
    for i, (label, mapping) in enumerate(parse_map):
        if i < len(ccat_parse):
            char = ccat_parse[i]
            if char != '-':
                value = mapping.get(char)
                if value:
                    result.append(f"{value}")
    return ", ".join(result) if result else ccat_parse

TAG_MAPS = {
    "ESV": {"book": "b", "chapter": "c", "verse": "v", "attr": "n"},
    "KJV": {"book": "book", "chapter": "chapter", "verse": "verse", "attr": "num"},
}

def get_verse_text_with_inline_tags(element):
    """
    Recursively get all text from an element, including text inside <i> and <span> tags,
    and all tail text after those tags, for proper KJV verse rendering.
    Ignores the tags themselves but includes their text and tails.
    """
    parts = []
    if element.text:
        parts.append(element.text)
    for child in element:
        # For <i> and <span> tags, include their text and tails
        parts.append(get_verse_text_with_inline_tags(child))
        if child.tail:
            parts.append(child.tail)
    return ''.join(parts)

def lookup_english_verse(book_name, chapter, verse, translation="ESV"):
    """
    Look up a verse from a specified file in the 'english' directory.
    Handles inline tags for KJV (e.g., <i>, <span>), including their text and tails.
    Tries all known abbreviations for the book before reporting missing book.
    """
    file_path = f"english/{translation.lower()}.xml"
    tags = TAG_MAPS.get(translation.upper(), TAG_MAPS["ESV"])
    # Try all possible book identifiers
    book_data = get_book_data(book_name)
    tried = set()
    tried.add(book_name)
    tried_abbrevs = []
    if book_data:
        # Try canonical, short, and KJV abbrevs
        candidates = [book_name]
        if isinstance(book_data, tuple):
            # Add all known abbreviations
            for val in book_data:
                if isinstance(val, str) and val not in candidates:
                    candidates.append(val)
        for candidate in candidates:
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()
                book_element = None
                for b in root.findall(f".//{tags['book']}"):
                    if b.get(tags['attr']) == str(candidate):
                        book_element = b
                        break
                if book_element is not None:
                    chapter_element = None
                    for c in book_element.findall(f".//{tags['chapter']}"):
                        if c.get(tags['attr']) == str(chapter):
                            chapter_element = c
                            break
                    if chapter_element is None:
                        return f"Chapter {chapter} not found in {candidate} ({translation})."
                    verse_element = None
                    for v in chapter_element.findall(f".//{tags['verse']}"):
                        if v.get(tags['attr']) == str(verse):
                            verse_element = v
                            break
                    if verse_element is None:
                        return f"Verse {verse} not found in {candidate} {chapter} ({translation})."
                    if translation.upper() == "KJV":
                        return get_verse_text_with_inline_tags(verse_element).strip()
                    return verse_element.text.strip() if verse_element.text else ""
            except FileNotFoundError:
                return f"Translation file '{translation.lower()}.xml' not found in 'english' directory."
            except ET.ParseError:
                return f"Error parsing the file '{translation.lower()}.xml'. Please check the file format."
    return f"Book '{book_name}' not found in {translation} translation."

USERDATA_DIR = "userdata"
USER_TRANSLATIONS_FILE = os.path.join(USERDATA_DIR, "usertranslations.json")

def load_user_translations():
    """Load user translations from a JSON file."""
    if not os.path.exists(USER_TRANSLATIONS_FILE):
        return {}
    with open(USER_TRANSLATIONS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

def save_user_translation(book, chapter, verse, translation):
    """Save a user translation to the JSON file."""
    os.makedirs(USERDATA_DIR, exist_ok=True)
    translations = load_user_translations()
    translations.setdefault(book, {}).setdefault(str(chapter), {})[str(verse)] = translation
    with open(USER_TRANSLATIONS_FILE, "w", encoding="utf-8") as file:
        json.dump(translations, file, indent=4)

def load_user_translation(book, chapter, verse):
    """Load a specific user translation from the JSON file."""
    if not os.path.exists(USER_TRANSLATIONS_FILE):
        return None  # Return None if the file doesn't exist

    with open(USER_TRANSLATIONS_FILE, "r", encoding="utf-8") as file:
        translations = json.load(file)

    # Navigate to the specific translation if it exists
    return translations.get(book, {}).get(str(chapter), {}).get(str(verse))

def get_greek_text(book, chapter, verse):
    """Retrieve the Greek text, words, and lemmas for a specific verse from MorphGNT data."""
    book_num = get_book_data(book)[0]  # Get the book number from NEW_TESTAMENT
    verse_text = []

    for row in morphgnt_rows(book_num):
        # Extract book, chapter, and verse from the 'bcv' key
        b, c, v = map(int, [row['bcv'][:2], row['bcv'][2:4], row['bcv'][4:]])

        if b == book_num and c == chapter and v == verse:
            # Collect the text, word, and lemma for the verse
            verse_text.append({
                'text': row['text'],
                'word': row['word'],
                'lemma': row['lemma'],
                'pos': row['ccat-pos'],
                'parse': row['ccat-parse']
            })

    return verse_text

def navigate_verse(current_book, current_chapter, current_verse, mode):
    """
    Master navigation function for moving between verses of the New Testament.
    Args:
        current_book (str|int): Book name, abbreviation, or number.
        current_chapter (int): Current chapter number.
        current_verse (int): Current verse number.
        mode (str): One of 'next_verse', 'previous_verse', 'start_of_chapter', 'start_of_next_chapter'.
    Returns:
        (book_name, chapter, verse): The target book, chapter, and verse after navigation.
    """
    # Get canonical book data
    book_data = get_book_data(current_book)
    if not book_data:
        raise ValueError(f"Unknown book: {current_book}")
    book_num = book_data[0]
    # Find the index of the book in NEW_TESTAMENT
    book_idx = None
    for idx, book in enumerate(NEW_TESTAMENT):
        if book[0] == book_num:
            book_idx = idx
            break
    if book_idx is None:
        raise ValueError(f"Book not found in NEW_TESTAMENT: {current_book}")
    # Helper to get max chapter and verse for a book
    def get_max_chapter(book_num):
        # Find the highest chapter number in the morphgnt_rows for this book
        max_chapter = 0
        for row in morphgnt_rows(book_num):
            c = int(row['bcv'][2:4])
            if c > max_chapter:
                max_chapter = c
        return max_chapter
    def get_max_verse(book_num, chapter):
        max_verse = 0
        for row in morphgnt_rows(book_num):
            c = int(row['bcv'][2:4])
            v = int(row['bcv'][4:])
            if c == chapter and v > max_verse:
                max_verse = v
        return max_verse
    # Navigation logic
    if mode == 'next_verse':
        max_verse = get_max_verse(book_num, current_chapter)
        if current_verse < max_verse:
            return (NUMBER_TO_DATA[book_num][0], current_chapter, current_verse + 1)
        else:
            max_chapter = get_max_chapter(book_num)
            if current_chapter < max_chapter:
                return (NUMBER_TO_DATA[book_num][0], current_chapter + 1, 1)
            elif book_idx < len(NEW_TESTAMENT) - 1:
                # Move to next book
                next_book = NEW_TESTAMENT[book_idx + 1]
                next_book_num = next_book[0]
                return (next_book[1], 1, 1)
            else:
                # At end of Revelation
                return (NUMBER_TO_DATA[book_num][0], current_chapter, current_verse)
    elif mode == 'previous_verse':
        if current_verse > 1:
            return (NUMBER_TO_DATA[book_num][0], current_chapter, current_verse - 1)
        elif current_chapter > 1:
            prev_chapter = current_chapter - 1
            prev_max_verse = get_max_verse(book_num, prev_chapter)
            return (NUMBER_TO_DATA[book_num][0], prev_chapter, prev_max_verse)
        elif book_idx > 0:
            # Move to previous book
            prev_book = NEW_TESTAMENT[book_idx - 1]
            prev_book_num = prev_book[0]
            prev_max_chapter = get_max_chapter(prev_book_num)
            prev_max_verse = get_max_verse(prev_book_num, prev_max_chapter)
            return (prev_book[1], prev_max_chapter, prev_max_verse)
        else:
            # At start of Matthew
            return (NUMBER_TO_DATA[book_num][0], current_chapter, current_verse)
    elif mode == 'start_of_chapter':
        if current_verse == 1:
            # Already at start of chapter, go to start of previous chapter if possible
            if current_chapter > 1:
                return (NUMBER_TO_DATA[book_num][0], current_chapter - 1, 1)
            elif book_idx > 0:
                # Move to previous book's last chapter
                prev_book = NEW_TESTAMENT[book_idx - 1]
                prev_book_num = prev_book[0]
                prev_max_chapter = get_max_chapter(prev_book_num)
                return (prev_book[1], prev_max_chapter, 1)
            else:
                # At very start of Matthew
                return (NUMBER_TO_DATA[book_num][0], current_chapter, current_verse)
        else:
            return (NUMBER_TO_DATA[book_num][0], current_chapter, 1)
    elif mode == 'start_of_next_chapter':
        max_chapter = get_max_chapter(book_num)
        if current_chapter < max_chapter:
            return (NUMBER_TO_DATA[book_num][0], current_chapter + 1, 1)
        elif book_idx < len(NEW_TESTAMENT) - 1:
            next_book = NEW_TESTAMENT[book_idx + 1]
            return (next_book[1], 1, 1)
        else:
            return (NUMBER_TO_DATA[book_num][0], current_chapter, current_verse)
    else:
        raise ValueError(f"Unknown navigation mode: {mode}")

