"""
Greek New Testament Translation Helper

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

---

This software uses the following third-party libraries:
- PyQt5 (GPL v3): Copyright (C) Riverbank Computing Limited
- lxml (BSD-like): Copyright (c) 2004-2024 ElementTree contributors, lxml contributors
"""

import sys
import os
import configparser
import webbrowser
import unicodedata
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QTextEdit, QLineEdit, QMessageBox, QStatusBar, QComboBox, QFileDialog, QAction, QMenuBar, QInputDialog
)
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QKeySequence
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtGui import QTextDocument
from data_structures import (
    load_user_translation, save_user_translation, lookup_english_verse, get_greek_text, parse_strongs_greek, lookup_entry_by_unicode, interpret_ccat_parse, interpret_ccat_pos, navigate_verse, NEW_TESTAMENT
)
import tempfile

class TranslationHelperGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Greek New Testament Translation Helper")
        self.resize(1300, 800)  # Increased window size
        self.current_book = "John"
        self.current_chapter = 1
        self.current_verse = 1
        self.translation_changed = False
        self.translation_name = "ESV"
        self.strongs_dict = parse_strongs_greek("strongsgreek.xml")
        self.config_path = os.path.join("userdata", "settings.ini")
        self.load_last_verse()
        self.sidebar_visible = False  # Track sidebar visibility
        self.init_ui()
        self.update_verse()
        self.user_name = self.load_user_name()
        self.init_menu_bar()

    def load_user_name(self):
        # Store user's name in settings.ini and prompt only if not present
        config = configparser.ConfigParser()
        if os.path.exists(self.config_path):
            config.read(self.config_path)
            if 'user' in config and 'name' in config['user']:
                return config['user']['name']
        # Prompt for name if not set
        name, ok = QInputDialog.getText(self, "User Name", "Enter your name for export titles:")
        if ok and name.strip():
            # Save to settings file for future use
            if os.path.exists(self.config_path):
                config.read(self.config_path)
            if 'user' not in config:
                config['user'] = {}
            config['user']['name'] = name.strip()
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as configfile:
                config.write(configfile)
            return name.strip()
        return "User"

    def init_menu_bar(self):
        menubar = self.menuBar() if hasattr(self, 'menuBar') else QMenuBar(self)
        export_menu = menubar.addMenu("Export")
        export_html_action = QAction("Export Range to HTML", self)
        export_html_action.triggered.connect(self.export_range_html)
        export_pdf_action = QAction("Export Range to PDF", self)
        export_pdf_action.triggered.connect(self.export_range_pdf)
        export_all_html_action = QAction("Export All User Translations to HTML", self)
        export_all_html_action.triggered.connect(self.export_all_html)
        export_menu.addAction(export_html_action)
        export_menu.addAction(export_pdf_action)
        export_menu.addAction(export_all_html_action)
        self.setMenuBar(menubar)

    def export_range_html(self):
        # Prompt for range (start/end chapter/verse, same book)
        book = self.current_book
        start_chapter, ok1 = QInputDialog.getInt(self, "Export Range", "Start chapter:", self.current_chapter, 1)
        if not ok1:
            return
        start_verse, ok2 = QInputDialog.getInt(self, "Export Range", "Start verse:", self.current_verse, 1)
        if not ok2:
            return
        end_chapter, ok3 = QInputDialog.getInt(self, "Export Range", "End chapter:", self.current_chapter, start_chapter)
        if not ok3:
            return
        end_verse, ok4 = QInputDialog.getInt(self, "Export Range", "End verse:", self.current_verse, 1)
        if not ok4:
            return
        html = self.build_range_html(book, start_chapter, start_verse, end_chapter, end_verse)
        filename = f"{book} {start_chapter}_{start_verse}-{end_chapter}_{end_verse}.html"
        filepath = os.path.join("userdata", filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        self.open_with_system_app(filepath)

    def export_range_pdf(self):
        # Prompt for range (start/end chapter/verse, same book)
        book = self.current_book
        start_chapter, ok1 = QInputDialog.getInt(self, "Export Range", "Start chapter:", self.current_chapter, 1)
        if not ok1:
            return
        start_verse, ok2 = QInputDialog.getInt(self, "Export Range", "Start verse:", self.current_verse, 1)
        if not ok2:
            return
        end_chapter, ok3 = QInputDialog.getInt(self, "Export Range", "End chapter:", self.current_chapter, start_chapter)
        if not ok3:
            return
        end_verse, ok4 = QInputDialog.getInt(self, "Export Range", "End verse:", self.current_verse, 1)
        if not ok4:
            return
        html = self.build_range_html(book, start_chapter, start_verse, end_chapter, end_verse)
        filename = f"{book} {start_chapter}_{start_verse}-{end_chapter}_{end_verse}.pdf"
        filepath = os.path.join("userdata", filename)
        doc = QTextDocument()
        doc.setHtml(html)
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(filepath)
        doc.print_(printer)
        self.open_with_system_app(filepath)

    def export_all_html(self):
        # Export all user translations to HTML with improved formatting
        from data_structures import load_user_translations
        translations = load_user_translations()
        html = f"<h1>{self.user_name}'s New Testament Translations</h1>"
        for book in translations:
            html += f"<h2>{book}</h2>"
            for chapter in sorted(translations[book], key=lambda x: int(x)):
                html += f"<h3>Chapter {chapter}</h3>"
                first_verse = True
                for verse in sorted(translations[book][chapter], key=lambda x: int(x)):
                    text = translations[book][chapter][verse]
                    if first_verse:
                        html += f"<b>{book} {chapter}:{verse}</b>: {text}<br>"
                        first_verse = False
                    else:
                        html += f"<b>{verse}:</b> {text}<br>"
        filename = f"{self.user_name}_all_translations.html"
        filepath = os.path.join("userdata", filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        self.open_with_system_app(filepath)

    def build_range_html(self, book, start_chapter, start_verse, end_chapter, end_verse):
        # Build HTML for a range of verses in one book using only the user's translation file, with improved formatting
        from data_structures import load_user_translations
        html = f"<h1>{self.user_name}'s translation of {book} {start_chapter}:{start_verse}-{end_chapter}:{end_verse}</h1>"
        translations = load_user_translations()
        if book not in translations:
            return html + "<br><i>(no translations for this book)</i>"
        def in_range(ch, vs):
            if (ch < start_chapter) or (ch > end_chapter):
                return False
            if ch == start_chapter and vs < start_verse:
                return False
            if ch == end_chapter and vs > end_verse:
                return False
            return True
        for ch_str in sorted(translations[book], key=lambda x: int(x)):
            ch = int(ch_str)
            verses_in_chapter = [int(vs) for vs in translations[book][ch_str].keys() if in_range(ch, int(vs))]
            if not verses_in_chapter:
                continue
            html += f"<h3>Chapter {ch}</h3>"
            first_verse = True
            for vs in sorted(verses_in_chapter):
                user_text = translations[book][ch_str][str(vs)]
                if first_verse:
                    html += f"<b>{book} {ch}:{vs}</b>: {user_text}<br>"
                    first_verse = False
                else:
                    html += f"<b>{vs}:</b> {user_text}<br>"
        return html

    def open_with_system_app(self, filepath):
        if sys.platform.startswith('win'):
            os.startfile(filepath)
        elif sys.platform.startswith('darwin'):
            os.system(f'open "{filepath}"')
        else:
            os.system(f'xdg-open "{filepath}"')

    def load_last_verse(self):
        config = configparser.ConfigParser()
        fallback = ("Matthew", 1, 1)
        if os.path.exists(self.config_path):
            try:
                config.read(self.config_path)
                if 'last_verse' in config:
                    book = config['last_verse'].get('book', fallback[0])
                    chapter = int(config['last_verse'].get('chapter', fallback[1]))
                    verse = int(config['last_verse'].get('verse', fallback[2]))
                    # Check if this reference exists
                    greek_text_data = get_greek_text(book, chapter, verse)
                    if greek_text_data:
                        self.current_book = book
                        self.current_chapter = chapter
                        self.current_verse = verse
                        return
            except Exception:
                pass  # If ini is corrupted or reference is invalid, fall back
        # Fallback to Matthew 1:1
        self.current_book, self.current_chapter, self.current_verse = fallback

    def save_last_verse(self):
        # Only save if the current reference is valid
        greek_text_data = get_greek_text(self.current_book, self.current_chapter, self.current_verse)
        if not greek_text_data:
            return  # Don't save invalid reference
        config = configparser.ConfigParser()
        # Read existing config to preserve user name and other settings
        if os.path.exists(self.config_path):
            config.read(self.config_path)
        config['last_verse'] = {
            'book': self.current_book,
            'chapter': str(self.current_chapter),
            'verse': str(self.current_verse)
        }
        config['window'] = {
            'x': str(self.x()),
            'y': str(self.y()),
            'width': str(self.width()),
            'height': str(self.height())
        }
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as configfile:
            config.write(configfile)

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        # --- Book, chapter, verse jump controls (now at the top) ---
        jump_layout = QHBoxLayout()
        self.book_input = QComboBox()
        self.book_input.setEditable(False)
        self.book_input.addItems([book[1] for book in NEW_TESTAMENT])
        self.book_input.setToolTip("Select a book")
        self.book_input.setStyleSheet("font-size: 24px")
        self.chapter_input = QLineEdit()
        self.chapter_input.setPlaceholderText("Chapter")
        self.chapter_input.setStyleSheet("font-size: 22px; min-width: 80px; padding: 8px 16px;")
        self.verse_input = QLineEdit()
        self.verse_input.setPlaceholderText("Verse")
        self.verse_input.setStyleSheet("font-size: 22px; min-width: 80px; padding: 8px 16px;")
        self.verse_input.returnPressed.connect(self.jump_to_reference)
        self.jump_button = QPushButton("Go to Reference")
        self.jump_button.setStyleSheet("font-size: 22px; padding: 8px 24px;")
        self.jump_button.clicked.connect(self.jump_to_reference)
        jump_layout.addWidget(self.book_input)
        jump_layout.addWidget(self.chapter_input)
        jump_layout.addWidget(self.verse_input)
        jump_layout.addWidget(self.jump_button)
        left_layout.addLayout(jump_layout)
        # --- Greek text ---
        self.greek_text = QLabel()
        self.greek_text.setWordWrap(True)
        self.greek_text.setStyleSheet("font-size: 28px; font-weight: bold; padding: 48px 64px 48px 64px; background: #fff; border-radius: 18px; margin: 24px 0px 24px 0px;")
        self.greek_text.setMinimumHeight(120)
        self.greek_text.setMaximumHeight(300)
        self.greek_text.setSizePolicy(self.greek_text.sizePolicy().horizontalPolicy(), 3)
        left_layout.addWidget(self.greek_text)
        # --- User translation ---
        self.translation_label = QLabel("Your Translation:")
        self.translation_input = QTextEdit()
        self.translation_input.setStyleSheet("font-size: 26px; padding: 40px 64px 40px 64px; background: #fff; border-radius: 18px; margin: 24px 0px 24px 0px;")
        self.translation_input.textChanged.connect(self.on_translation_changed)
        left_layout.addWidget(self.translation_label)
        left_layout.addWidget(self.translation_input)
        self.save_button = QPushButton("Save Translation")
        self.save_button.setStyleSheet("font-size: 22px;")
        self.save_button.clicked.connect(self.save_translation)
        left_layout.addWidget(self.save_button)
        # --- Compare and Word Lookup buttons side by side ---
        compare_lookup_layout = QHBoxLayout()
        self.compare_button = QPushButton("Show Standard Translations")
        self.compare_button.setStyleSheet("font-size: 22px;")
        self.compare_button.clicked.connect(self.show_standard_sidebar)
        self.lookup_button = QPushButton("Show Word Helpers")
        self.lookup_button.setStyleSheet("font-size: 22px;")
        self.lookup_button.clicked.connect(self.show_lookup_sidebar)
        compare_lookup_layout.addWidget(self.compare_button)
        compare_lookup_layout.addWidget(self.lookup_button)
        left_layout.addLayout(compare_lookup_layout)
        # Navigation buttons with chapter jumpers
        nav_layout = QHBoxLayout()
        self.prev_chapter_button = QPushButton("⏮")
        self.prev_chapter_button.setToolTip("Go to start of previous chapter")
        self.prev_chapter_button.setStyleSheet("font-size: 22px;")
        self.prev_chapter_button.clicked.connect(self.start_of_previous_chapter)
        self.prev_button = QPushButton("← Previous Verse")
        self.prev_button.setStyleSheet("font-size: 22px;")
        self.prev_button.clicked.connect(self.previous_verse)
        self.next_button = QPushButton("Next Verse →")
        self.next_button.setStyleSheet("font-size: 22px;")
        self.next_button.clicked.connect(self.next_verse)
        self.next_chapter_button = QPushButton("⏭")
        self.next_chapter_button.setToolTip("Go to start of next chapter")
        self.next_chapter_button.setStyleSheet("font-size: 22px;")
        self.next_chapter_button.clicked.connect(self.start_of_next_chapter)
        nav_layout.addWidget(self.prev_chapter_button)
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.next_button)
        nav_layout.addWidget(self.next_chapter_button)
        left_layout.addLayout(nav_layout)
        # --- Sidebars ---
        self.sidebar_widget = QWidget()
        self.sidebar_layout = QVBoxLayout()
        self.sidebar_widget.setLayout(self.sidebar_layout)
        # Remove fixed width settings; let layout manage width
        # self.sidebar_widget.setMinimumWidth(int(self.width() * 0.4))
        # self.sidebar_widget.setMaximumWidth(int(self.width() * 0.4))
        # --- Standard translation sidebar ---
        self.standard_text = QLabel()
        self.standard_text.setWordWrap(True)
        self.standard_text.setStyleSheet("font-size: 20px; color: #333; padding: 8px 16px 8px 16px;")
        # --- Word lookup sidebar ---
        self.lookup_label = QLabel("Choose a word to see details:")
        self.word_list = QListWidget()
        self.word_list.currentRowChanged.connect(self.display_word_info)
        self.lookup_info = QTextEdit()
        self.lookup_info.setReadOnly(True)
        self.wiktionary_button = QPushButton("Wiktionary")
        self.wiktionary_button.setStyleSheet("font-size: 22px;")
        self.wiktionary_button.clicked.connect(self.open_wiktionary)
        # --- Add sidebar to main layout ---
        main_layout.addLayout(left_layout, 3)
        main_layout.addWidget(self.sidebar_widget, 2)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.installEventFilter(self)
        self.hide_sidebar()  # Only clear sidebar contents, not the widget itself

    def show_status(self, message, timeout=2000):
        self.status_bar.showMessage(message, timeout)

    def toggle_sidebar(self):
        self.sidebar_visible = not self.sidebar_visible
        if self.sidebar_visible:
            self.lookup_label.show()
            self.word_list.show()
            self.lookup_info.show()
            self.wiktionary_button.show()
            self.toggle_sidebar_button.setText("Hide Word Helpers")
        else:
            self.lookup_label.hide()
            self.word_list.hide()
            self.lookup_info.hide()
            self.wiktionary_button.hide()
            self.toggle_sidebar_button.setText("Show Word Helpers")

    def update_verse(self):
        self.save_last_verse()
        greek_text_data = get_greek_text(self.current_book, self.current_chapter, self.current_verse)
        greek_text = " ".join([word['text'] for word in greek_text_data])
        # Update the jump controls to reflect the current verse
        idx = self.book_input.findText(self.current_book)
        if idx != -1:
            self.book_input.setCurrentIndex(idx)
        self.chapter_input.setText(str(self.current_chapter))
        self.verse_input.setText(str(self.current_verse))
        self.greek_text.setText(greek_text)
        # Hide sidebar and reset buttons after navigation
        self.hide_sidebar()
        user_translation = load_user_translation(self.current_book, self.current_chapter, self.current_verse) or ""
        self.translation_input.setText(user_translation)
        self.translation_changed = False
        # Populate word list
        self.word_list.clear()
        self._sidebar_lemmas = [word['lemma'] for word in greek_text_data]
        self._sidebar_pos = [word['pos'] for word in greek_text_data]
        self._sidebar_parse = [word['parse'] for word in greek_text_data]
        for word in greek_text_data:
            self.word_list.addItem(word['word'])
        self.lookup_info.clear()
        self.translation_input.setFocus()
        self.show_status(f"Viewing {self.current_book} {self.current_chapter}:{self.current_verse}")
        # Tooltips
        self.prev_button.setToolTip("Go to previous verse")
        self.next_button.setToolTip("Go to next verse")
        self.jump_button.setToolTip("Jump to a specific book, chapter, and verse")
        self.save_button.setToolTip("Save your translation for this verse")
        self.compare_button.setToolTip("Show the standard translation for this verse")
        self.lookup_button.setToolTip("Show the word lookup sidebar")
        #self.hide_standard_button.setToolTip("Hide the standard translation sidebar")
        self.translation_input.setToolTip("Type your translation here")
        self.word_list.setToolTip("Select a Greek word to see lexical and parsing info")
        self.lookup_info.setToolTip("Lexical and parsing info for the selected word")
        # Do NOT auto-select the first word in the word list

    def show_standard_sidebar(self):
        if self.compare_button.text() == "Hide Standard Translations":
            self.hide_sidebar()
            return
        self.compare_button.setText("Hide Standard Translations")
        self.lookup_button.setText("Show Word Helpers")
        # Clear sidebar and add standard translation
        while self.sidebar_layout.count():
            item = self.sidebar_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
        self.standard_text.setText("")
        esv_translation = lookup_english_verse(self.current_book, self.current_chapter, self.current_verse, "ESV")
        kjv_translation = lookup_english_verse(self.current_book, self.current_chapter, self.current_verse, "KJV")
        self.standard_text.setText(f"<b>ESV:</b> {esv_translation}<br><br><b>KJV:</b> {kjv_translation}")
        self.sidebar_layout.addWidget(self.standard_text)
        # Always keep sidebar_widget visible
        self.sidebar_widget.setVisible(True)
        self.compare_button.setEnabled(True)
        self.lookup_button.setEnabled(True)

    def show_lookup_sidebar(self):
        if self.lookup_button.text() == "Hide Word Helpers":
            self.hide_sidebar()
            return
        self.lookup_button.setText("Hide Word Helpers")
        self.compare_button.setText("Show Standard Translations")
        # Clear sidebar and add lookup widgets
        while self.sidebar_layout.count():
            item = self.sidebar_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
        self.sidebar_layout.addWidget(self.lookup_label)
        self.sidebar_layout.addWidget(self.word_list)
        self.sidebar_layout.addWidget(self.lookup_info)
        self.sidebar_layout.addWidget(self.wiktionary_button)
        # Always keep sidebar_widget visible
        self.sidebar_widget.setVisible(True)
        self.compare_button.setEnabled(True)
        self.lookup_button.setEnabled(True)

    def hide_sidebar(self):
        # Do not hide the sidebar widget; just clear its contents
        while self.sidebar_layout.count():
            item = self.sidebar_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
        self.compare_button.setText("Show Standard Translations")
        self.lookup_button.setText("Show Word Helpers")
        self.compare_button.setEnabled(True)
        self.lookup_button.setEnabled(True)

    def save_last_verse(self):
        # Only save if the current reference is valid
        greek_text_data = get_greek_text(self.current_book, self.current_chapter, self.current_verse)
        if not greek_text_data:
            return  # Don't save invalid reference
        config = configparser.ConfigParser()
        # Read existing config to preserve user name and other settings
        if os.path.exists(self.config_path):
            config.read(self.config_path)
        config['last_verse'] = {
            'book': self.current_book,
            'chapter': str(self.current_chapter),
            'verse': str(self.current_verse)
        }
        config['window'] = {
            'x': str(self.x()),
            'y': str(self.y()),
            'width': str(self.width()),
            'height': str(self.height())
        }
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as configfile:
            config.write(configfile)

    def load_last_verse(self):
        config = configparser.ConfigParser()
        fallback = ("Matthew", 1, 1)
        if os.path.exists(self.config_path):
            try:
                config.read(self.config_path)
                if 'last_verse' in config:
                    book = config['last_verse'].get('book', fallback[0])
                    chapter = int(config['last_verse'].get('chapter', fallback[1]))
                    verse = int(config['last_verse'].get('verse', fallback[2]))
                    greek_text_data = get_greek_text(book, chapter, verse)
                    if greek_text_data:
                        self.current_book = book
                        self.current_chapter = chapter
                        self.current_verse = verse
                if 'window' in config:
                    x = int(config['window'].get('x', '100'))
                    y = int(config['window'].get('y', '100'))
                    width = int(config['window'].get('width', '1300'))
                    height = int(config['window'].get('height', '800'))
                    self.setGeometry(x, y, width, height)
                    self.resize(width, height)
                    self.move(x, y)
                    return
            except Exception:
                pass
        self.current_book, self.current_chapter, self.current_verse = fallback
        self.setGeometry(100, 100, 1300, 800)
        self.resize(1300, 800)
        self.move(100, 100)

    def on_translation_changed(self):
        self.translation_changed = True

    def save_translation(self):
        user_translation = self.translation_input.toPlainText()
        save_user_translation(self.current_book, self.current_chapter, self.current_verse, user_translation)
        self.translation_changed = False
        self.show_status(f"Saved translation for {self.current_book} {self.current_chapter}:{self.current_verse}.")

    def maybe_save_translation(self):
        if self.translation_changed:
            reply = QMessageBox.question(self, "Save Translation?", "You have unsaved changes. Save before navigating?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                self.save_translation()
                return True
            elif reply == QMessageBox.No:
                self.translation_changed = False
                return True
            else:
                return False
        return True

    def closeEvent(self, event):
        if not self.maybe_save_translation():
            event.ignore()
        else:
            event.accept()

    def next_verse(self):
        if not self.maybe_save_translation():
            return
        self.current_book, self.current_chapter, self.current_verse = navigate_verse(
            self.current_book, self.current_chapter, self.current_verse, 'next_verse')
        self.update_verse()

    def previous_verse(self):
        if not self.maybe_save_translation():
            return
        self.current_book, self.current_chapter, self.current_verse = navigate_verse(
            self.current_book, self.current_chapter, self.current_verse, 'previous_verse')
        self.update_verse()

    def start_of_previous_chapter(self):
        if not self.maybe_save_translation():
            return
        self.current_book, self.current_chapter, self.current_verse = navigate_verse(
            self.current_book, self.current_chapter, self.current_verse, 'start_of_chapter')
        self.update_verse()

    def start_of_next_chapter(self):
        if not self.maybe_save_translation():
            return
        self.current_book, self.current_chapter, self.current_verse = navigate_verse(
            self.current_book, self.current_chapter, self.current_verse, 'start_of_next_chapter')
        self.update_verse()

    def jump_to_reference(self):
        book = self.book_input.currentText() if isinstance(self.book_input, QComboBox) else self.book_input.text().strip()
        chapter = self.chapter_input.text().strip()
        verse = self.verse_input.text().strip()
        if not book or not chapter.isdigit() or not verse.isdigit():
            QMessageBox.warning(self, "Invalid Reference", "Please enter a valid book, chapter, and verse.")
            return
        chapter = int(chapter)
        verse = int(verse)
        greek_text_data = get_greek_text(book, chapter, verse)
        if not greek_text_data:
            QMessageBox.warning(self, "Reference Not Found", f"No Greek text found for {book} {chapter}:{verse}. Please check your reference.")
            return
        self.current_book = book
        self.current_chapter = chapter
        self.current_verse = verse
        self.update_verse()

    def display_word_info(self, idx):
        if idx < 0 or idx >= len(self._sidebar_lemmas):
            self.lookup_info.clear()
            return
        lemma = self._sidebar_lemmas[idx]
        pos = interpret_ccat_pos(self._sidebar_pos[idx])
        parse = interpret_ccat_parse(self._sidebar_parse[idx])
        info = f"<div style='font-size:17px'><h2>{self.word_list.item(idx).text()}</h2><b>Part of Speech:</b> {pos}"
        info += f"<br><b>Parsing:</b> {parse}"
        entry = lookup_entry_by_unicode(lemma, self.strongs_dict)
        if entry:
            definition = entry.get('definition', '')
            pronunciation = entry.get('pronunciation', '')
            transliteration = entry.get('transliteration', '')
            info += f"<br><br><b>Dictionary form:</b> {lemma}<br><b>Definition:</b> {definition}"
            if transliteration:
                info += f"<br><b>Transliteration:</b> {transliteration}"
            if pronunciation:
                info += f"<br><b>Pronunciation:</b> {pronunciation}"
            info += "</div>"
        else:
            info = f"<div style='font-size:17px'>No entry found for lemma: {lemma}</div>"
        self.lookup_info.setHtml(info)

    def open_wiktionary(self):
        idx = self.word_list.currentRow()
        if idx < 0 or idx >= len(self._sidebar_lemmas):
            QMessageBox.information(self, "No Word Selected", "Please select a word from the list first.")
            return
        lemma = self._sidebar_lemmas[idx]
        normalised_lemma = unicodedata.normalize("NFC", lemma)
        url = f"https://en.wiktionary.org/wiki/{normalised_lemma}#Ancient_Greek"
        webbrowser.open(url)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            key = event.key()
            modifiers = event.modifiers()
            # Ctrl+S: Save
            if key == Qt.Key_S and modifiers & Qt.ControlModifier:
                self.save_translation()
                return True
            # Alt+Left: Previous verse
            if key == Qt.Key_Left and modifiers & Qt.AltModifier:
                self.previous_verse()
                return True
            # Alt+Right: Next verse
            if key == Qt.Key_Right and modifiers & Qt.AltModifier:
                self.next_verse()
                return True
            # Ctrl+PgUp: Start of previous chapter
            if key == Qt.Key_PageUp and modifiers & Qt.ControlModifier:
                self.start_of_previous_chapter()
                return True
            # Ctrl+PgDn: Start of next chapter
            if key == Qt.Key_PageDown and modifiers & Qt.ControlModifier:
                self.start_of_next_chapter()
                return True
        return super().eventFilter(obj, event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TranslationHelperGUI()
    window.show()
    sys.exit(app.exec_())
