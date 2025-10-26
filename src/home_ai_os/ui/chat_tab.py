"""Chat tab for LLM interaction."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QLabel, QComboBox, QGroupBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from loguru import logger

try:
    from home_ai_os.llm.ollama_client import get_ollama_client
except ImportError as e:
    logger.warning(f"LLM module not available: {e}")
    get_ollama_client = None


class ChatThread(QThread):
    """Thread for LLM chat to avoid blocking UI."""
    
    response_chunk = pyqtSignal(str)
    response_complete = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, ollama_client, model, prompt):
        super().__init__()
        self.ollama_client = ollama_client
        self.model = model
        self.prompt = prompt
    
    def run(self):
        """Run chat in background."""
        try:
            response = self.ollama_client.chat(
                model=self.model,
                messages=[{"role": "user", "content": self.prompt}],
                stream=True
            )
            
            for chunk in response:
                if "message" in chunk and "content" in chunk["message"]:
                    self.response_chunk.emit(chunk["message"]["content"])
            
            self.response_complete.emit()
        
        except Exception as e:
            self.error_occurred.emit(str(e))


class ChatTab(QWidget):
    """Chat interface tab."""
    
    def __init__(self):
        super().__init__()
        
        self.ollama = None
        if get_ollama_client:
            try:
                self.ollama = get_ollama_client()
            except Exception as e:
                logger.error(f"Could not initialize Ollama client: {e}")
        
        self.chat_thread = None
        self.conversation_history = []
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        
        header = QLabel("AI Chat Interface")
        header.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addWidget(header)
        
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "mistral:7b-instruct",
            "llama3.2:3b",
            "phi3:mini",
            "codellama:13b"
        ])
        model_layout.addWidget(self.model_combo)
        
        model_layout.addStretch()
        
        self.clear_btn = QPushButton("🗑️ Clear History")
        self.clear_btn.clicked.connect(self.clear_history)
        model_layout.addWidget(self.clear_btn)
        
        layout.addLayout(model_layout)
        
        chat_group = QGroupBox("Conversation")
        chat_layout = QVBoxLayout()
        
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setPlaceholderText("Chat history will appear here...")
        chat_layout.addWidget(self.chat_display)
        
        chat_group.setLayout(chat_layout)
        layout.addWidget(chat_group)
        
        input_layout = QHBoxLayout()
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your message here...")
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        
        self.send_btn = QPushButton("📤 Send")
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn)
        
        layout.addLayout(input_layout)
        
        self.setLayout(layout)
        
        if self.ollama:
            self.chat_display.append("✓ Connected to Ollama")
            self.chat_display.append("💬 Ready to chat! Type a message and press Enter.\n")
        else:
            self.chat_display.append("❌ Ollama not available")
            self.chat_display.append("Please install Ollama: https://ollama.ai\n")
            self.send_btn.setEnabled(False)
            self.input_field.setEnabled(False)
    
    def send_message(self):
        """Send message to LLM."""
        if not self.ollama:
            self.chat_display.append("❌ Ollama not available\n")
            return
        
        message = self.input_field.text().strip()
        if not message:
            return
        
        self.chat_display.append(f"<b>You:</b> {message}\n")
        self.input_field.clear()
        
        self.send_btn.setEnabled(False)
        self.input_field.setEnabled(False)
        
        model = self.model_combo.currentText()
        self.chat_thread = ChatThread(self.ollama, model, message)
        self.chat_thread.response_chunk.connect(self.on_response_chunk)
        self.chat_thread.response_complete.connect(self.on_response_complete)
        self.chat_thread.error_occurred.connect(self.on_error)
        
        self.chat_display.append(f"<b>AI ({model}):</b> ")
        self.chat_thread.start()
    
    def on_response_chunk(self, chunk):
        """Handle response chunk from LLM."""
        cursor = self.chat_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(chunk)
        self.chat_display.setTextCursor(cursor)
        self.chat_display.ensureCursorVisible()
    
    def on_response_complete(self):
        """Handle response completion."""
        self.chat_display.append("\n")
        self.send_btn.setEnabled(True)
        self.input_field.setEnabled(True)
        self.input_field.setFocus()
    
    def on_error(self, error):
        """Handle error."""
        self.chat_display.append(f"\n❌ Error: {error}\n")
        self.send_btn.setEnabled(True)
        self.input_field.setEnabled(True)
        logger.error(f"Chat error: {error}")
    
    def clear_history(self):
        """Clear chat history."""
        self.chat_display.clear()
        self.conversation_history = []
        self.chat_display.append("💬 Chat history cleared. Ready for new conversation.\n")
