import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QListWidget, 
                             QTextEdit, QFrame, QProgressBar, QFileDialog,
                             QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import os

class TuitionNotesGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.uploaded_files = []
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Tuition Invoice Generator")
        self.setGeometry(100, 100, 900, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        self.create_header(main_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)
        
        # File upload section
        self.create_file_section(main_layout)
        
        # Notes section
        self.create_notes_section(main_layout)
        
        # Action buttons
        self.create_action_buttons(main_layout)
        
        # Status bar
        self.create_status_bar()
        
        # Apply stylesheet
        self.apply_styles()
        
    def create_header(self, layout):
        header_layout = QVBoxLayout()
        
        title = QLabel("📄 Tuition Invoice Generator")
        title.setFont(QFont("Helvetica", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)
        
        subtitle = QLabel("Upload CSV files and generate professional invoices")
        subtitle.setFont(QFont("Helvetica", 10))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #7f8c8d;")
        header_layout.addWidget(subtitle)
        
        layout.addLayout(header_layout)
        
    def create_file_section(self, layout):
        # Section header
        header_layout = QHBoxLayout()
        
        section_label = QLabel("📂 CSV Files")
        section_label.setFont(QFont("Helvetica", 12, QFont.Bold))
        header_layout.addWidget(section_label)
        
        self.file_count_label = QLabel("(0 files)")
        self.file_count_label.setStyleSheet("color: #95a5a6;")
        header_layout.addWidget(self.file_count_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        upload_btn = QPushButton("📁 Add File")
        upload_btn.clicked.connect(self.upload_file)
        button_layout.addWidget(upload_btn)
        
        upload_multiple_btn = QPushButton("📁 Add Multiple Files")
        upload_multiple_btn.clicked.connect(self.upload_multiple_files)
        button_layout.addWidget(upload_multiple_btn)
        
        clear_btn = QPushButton("🗑️ Clear All")
        clear_btn.clicked.connect(self.clear_all_files)
        button_layout.addWidget(clear_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # File list
        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(150)
        self.file_list.itemSelectionChanged.connect(self.on_file_select)
        layout.addWidget(self.file_list)
        
        # File actions
        file_actions_layout = QHBoxLayout()
        
        remove_btn = QPushButton("➖ Remove Selected")
        remove_btn.clicked.connect(self.remove_selected_file)
        file_actions_layout.addWidget(remove_btn)
        
        file_actions_layout.addStretch()
        
        self.file_details_label = QLabel("")
        self.file_details_label.setStyleSheet("color: #7f8c8d; font-size: 9pt;")
        file_actions_layout.addWidget(self.file_details_label)
        
        layout.addLayout(file_actions_layout)
        
    def create_notes_section(self, layout):
        # Section header
        header_layout = QHBoxLayout()
        
        section_label = QLabel("📝 Additional Notes (Optional)")
        section_label.setFont(QFont("Helvetica", 12, QFont.Bold))
        header_layout.addWidget(section_label)
        
        header_layout.addStretch()
        
        self.char_count_label = QLabel("0 characters")
        self.char_count_label.setStyleSheet("color: #95a5a6; font-size: 9pt;")
        header_layout.addWidget(self.char_count_label)
        
        layout.addLayout(header_layout)
        
        # Notes text area
        self.notes_text = QTextEdit()
        self.notes_text.setMinimumHeight(120)
        self.notes_text.setPlaceholderText(
            "Enter any additional notes or instructions for the invoice...\n"
            "For example: payment terms, special discounts, or reminders."
        )
        self.notes_text.textChanged.connect(self.update_char_count)
        layout.addWidget(self.notes_text)
        
        # Quick templates
        template_layout = QHBoxLayout()
        
        template_label = QLabel("Quick Templates:")
        template_label.setFont(QFont("Helvetica", 9))
        template_layout.addWidget(template_label)
        
        template_btn1 = QPushButton("Payment Due")
        template_btn1.clicked.connect(
            lambda: self.insert_template("Payment due within 7 days.")
        )
        template_layout.addWidget(template_btn1)
        
        template_btn2 = QPushButton("Thank You")
        template_btn2.clicked.connect(
            lambda: self.insert_template("Thank you for your continued trust!")
        )
        template_layout.addWidget(template_btn2)
        
        template_layout.addStretch()
        
        clear_notes_btn = QPushButton("Clear")
        clear_notes_btn.clicked.connect(self.clear_notes)
        template_layout.addWidget(clear_notes_btn)
        
        layout.addLayout(template_layout)
        
    def create_action_buttons(self, layout):
        button_layout = QHBoxLayout()
        
        settings_btn = QPushButton("⚙️ Settings")
        settings_btn.clicked.connect(self.open_settings)
        button_layout.addWidget(settings_btn)
        
        button_layout.addStretch()
        
        self.preview_btn = QPushButton("Preview")
        self.preview_btn.clicked.connect(self.preview_invoices)
        self.preview_btn.setEnabled(False)
        button_layout.addWidget(self.preview_btn)
        
        self.generate_btn = QPushButton("Generate Invoices")
        self.generate_btn.clicked.connect(self.generate_invoices)
        self.generate_btn.setEnabled(False)
        self.generate_btn.setStyleSheet(
            "QPushButton { font-weight: bold; padding: 12px 24px; color: black; }"
        )
        button_layout.addWidget(self.generate_btn)
        
        layout.addLayout(button_layout)
        
    def create_status_bar(self):
        self.status_bar = self.statusBar()
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #27ae60; padding: 5px;")
        self.status_bar.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            QPushButton {
                background-color: #3498db;
                color: black;
                border: none;
                padding: 12px 24px;
                border-radius: 4px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                padding: 12px 24px;
                color: black;
            }
            QListWidget {
                background-color: #ecf0f1;
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                padding: 5px;
                color: black;
            }
            QTextEdit {
                background-color: #ecf0f1;
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                padding: 10px;
                font-size: 10pt;
                color: black;
            }
        """)
        
    # Event handlers
    def upload_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV File",
            "",
            "CSV files (*.csv);;All files (*.*)"
        )
        
        if filename:
            self.uploaded_files.append(filename)
            self.update_file_list()
            self.update_status(f"Added: {os.path.basename(filename)}", "success")
            
    def upload_multiple_files(self):
        filenames, _ = QFileDialog.getOpenFileNames(
            self,
            "Select CSV Files",
            "",
            "CSV files (*.csv);;All files (*.*)"
        )
        
        if filenames:
            self.uploaded_files.extend(filenames)
            self.update_file_list()
            self.update_status(f"Added {len(filenames)} files", "success")
            
    def remove_selected_file(self):
        current_row = self.file_list.currentRow()
        if current_row >= 0:
            removed_file = self.uploaded_files.pop(current_row)
            self.update_file_list()
            self.update_status(f"Removed: {os.path.basename(removed_file)}", "info")
            
    def clear_all_files(self):
        if self.uploaded_files:
            self.uploaded_files.clear()
            self.update_file_list()
            self.update_status("All files cleared", "info")
            
    def update_file_list(self):
        self.file_list.clear()
        
        for file_path in self.uploaded_files:
            filename = os.path.basename(file_path)
            self.file_list.addItem(f"  📄 {filename}")
        
        count = len(self.uploaded_files)
        self.file_count_label.setText(f"({count} file{'s' if count != 1 else ''})")
        
        enabled = count > 0
        self.generate_btn.setEnabled(enabled)
        self.preview_btn.setEnabled(enabled)
        
    def on_file_select(self):
        current_row = self.file_list.currentRow()
        if current_row > 0:
            file_path = self.uploaded_files[current_row]
            file_size = os.path.getsize(file_path)
            size_kb = file_size / 1024
            self.file_details_label.setText(
                f"Size: {size_kb:.1f} KB | Path: {file_path}"
            )
            
    def update_char_count(self):
        char_count = len(self.notes_text.toPlainText())
        self.char_count_label.setText(f"{char_count} characters")
        
    def insert_template(self, template_text):
        self.notes_text.append(template_text)
        
    def clear_notes(self):
        self.notes_text.clear()
        
    def get_notes_content(self):
        return self.notes_text.toPlainText().strip()
        
    def generate_invoices(self):
        # TODO: Implement your generation logic
        if not self.uploaded_files:
            self.update_status("No files to process", "error")
            return
        
        notes = self.get_notes_content()
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.update_status("Generating invoices...", "processing")
        
        # TODO: Add your logic here
        
    def preview_invoices(self):
        # TODO: Implement preview
        self.update_status("Preview feature coming soon...", "info")
        
    def open_settings(self):
        # TODO: Implement settings
        self.update_status("Settings feature coming soon...", "info")
        
    def update_status(self, message, status_type="info"):
        colors = {
            "success": "#27ae60",
            "error": "#e74c3c",
            "warning": "#f39c12",
            "info": "#3498db",
            "processing": "#9b59b6"
        }
        
        color = colors.get(status_type, "#7f8c8d")
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color}; padding: 5px;")


def main():
    app = QApplication(sys.argv)
    window = TuitionNotesGenerator()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()