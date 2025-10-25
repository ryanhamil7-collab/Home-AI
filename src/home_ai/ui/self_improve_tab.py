"""Self-Improvement tab for the unified GUI."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QListWidget, QListWidgetItem, QGroupBox,
    QProgressBar, QMessageBox, QDialog, QDialogButtonBox,
    QScrollArea, QFrame, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from loguru import logger

from home_ai.self_improve.orchestrator import get_orchestrator


class AnalysisWorker(QThread):
    """Worker thread for code analysis."""
    
    finished = pyqtSignal(list)  # List of proposal IDs
    error = pyqtSignal(str)
    
    def __init__(self, max_files: int = 5):
        super().__init__()
        self.max_files = max_files
    
    def run(self):
        """Run analysis."""
        try:
            orchestrator = get_orchestrator()
            proposal_ids = orchestrator.analyze_and_propose(max_files=self.max_files)
            self.finished.emit(proposal_ids)
        except Exception as e:
            logger.error(f"Analysis worker error: {e}")
            self.error.emit(str(e))


class ProposalWidget(QFrame):
    """Widget for displaying a single proposal."""
    
    approved = pyqtSignal(str)  # proposal_id
    rejected = pyqtSignal(str)  # proposal_id
    applied = pyqtSignal(str)  # proposal_id
    rolled_back = pyqtSignal(str)  # proposal_id
    
    def __init__(self, proposal_data: dict, parent=None):
        super().__init__(parent)
        self.proposal_data = proposal_data
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI."""
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(2)
        
        layout = QVBoxLayout(self)
        
        header_layout = QHBoxLayout()
        
        proposal = self.proposal_data["proposal"]
        validation = self.proposal_data["validation"]
        status = self.proposal_data["status"]
        
        id_label = QLabel(f"<b>{proposal['id']}</b>")
        header_layout.addWidget(id_label)
        
        status_label = QLabel(f"Status: {status.upper()}")
        status_label.setStyleSheet(self._get_status_style(status))
        header_layout.addWidget(status_label)
        
        risk_label = QLabel(f"Risk: {proposal['risk_level'].upper()}")
        risk_label.setStyleSheet(self._get_risk_style(proposal['risk_level']))
        header_layout.addWidget(risk_label)
        
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        desc_label = QLabel(f"<b>Description:</b> {proposal['description']}")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        info_label = QLabel(
            f"<b>File:</b> {proposal['file_path']} | "
            f"<b>Scope:</b> {proposal['scope_files']} files, {proposal['scope_lines']} lines"
        )
        layout.addWidget(info_label)
        
        validation_group = QGroupBox("Validation Results")
        validation_layout = QVBoxLayout()
        
        risk_score = validation['risk_score']
        risk_bar = QProgressBar()
        risk_bar.setMaximum(100)
        risk_bar.setValue(int(risk_score * 100))
        risk_bar.setFormat(f"Risk Score: {risk_score:.2f}")
        
        if risk_score < 0.3:
            risk_bar.setStyleSheet("QProgressBar::chunk { background-color: #4CAF50; }")
        elif risk_score < 0.7:
            risk_bar.setStyleSheet("QProgressBar::chunk { background-color: #FFC107; }")
        else:
            risk_bar.setStyleSheet("QProgressBar::chunk { background-color: #F44336; }")
        
        validation_layout.addWidget(risk_bar)
        
        checks_text = "Checks: "
        for check_name, passed in validation['checks'].items():
            if isinstance(passed, bool):
                status_icon = "✅" if passed else "❌"
                checks_text += f"{status_icon} {check_name}  "
        
        checks_label = QLabel(checks_text)
        validation_layout.addWidget(checks_label)
        
        if validation['errors']:
            errors_label = QLabel(f"<b style='color: red;'>Errors ({len(validation['errors'])}):</b>")
            validation_layout.addWidget(errors_label)
            
            for error in validation['errors'][:3]:  # Show first 3
                error_label = QLabel(f"  • {error}")
                error_label.setWordWrap(True)
                validation_layout.addWidget(error_label)
        
        if validation['warnings']:
            warnings_label = QLabel(f"<b style='color: orange;'>Warnings ({len(validation['warnings'])}):</b>")
            validation_layout.addWidget(warnings_label)
            
            for warning in validation['warnings'][:3]:  # Show first 3
                warning_label = QLabel(f"  • {warning}")
                warning_label.setWordWrap(True)
                validation_layout.addWidget(warning_label)
        
        validation_group.setLayout(validation_layout)
        layout.addWidget(validation_group)
        
        diff_group = QGroupBox("Proposed Changes")
        diff_layout = QVBoxLayout()
        
        diff_text = QTextEdit()
        diff_text.setReadOnly(True)
        diff_text.setMaximumHeight(150)
        diff_text.setPlainText(self.proposal_data.get('diff', 'No diff available'))
        diff_text.setStyleSheet("font-family: monospace; font-size: 10pt;")
        
        diff_layout.addWidget(diff_text)
        diff_group.setLayout(diff_layout)
        layout.addWidget(diff_group)
        
        button_layout = QHBoxLayout()
        
        if status == "pending":
            approve_btn = QPushButton("✅ Approve")
            approve_btn.clicked.connect(lambda: self.approved.emit(proposal['id']))
            approve_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
            button_layout.addWidget(approve_btn)
            
            reject_btn = QPushButton("❌ Reject")
            reject_btn.clicked.connect(lambda: self.rejected.emit(proposal['id']))
            reject_btn.setStyleSheet("background-color: #F44336; color: white; padding: 8px;")
            button_layout.addWidget(reject_btn)
        
        elif status == "approved":
            apply_btn = QPushButton("🚀 Apply Changes")
            apply_btn.clicked.connect(lambda: self.applied.emit(proposal['id']))
            apply_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 8px;")
            button_layout.addWidget(apply_btn)
        
        elif status == "applied":
            rollback_btn = QPushButton("↩️ Rollback")
            rollback_btn.clicked.connect(lambda: self.rolled_back.emit(proposal['id']))
            rollback_btn.setStyleSheet("background-color: #FF9800; color: white; padding: 8px;")
            button_layout.addWidget(rollback_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def _get_status_style(self, status: str) -> str:
        """Get style for status label."""
        colors = {
            "pending": "#FFC107",
            "approved": "#4CAF50",
            "rejected": "#F44336",
            "applied": "#2196F3"
        }
        color = colors.get(status, "#9E9E9E")
        return f"background-color: {color}; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;"
    
    def _get_risk_style(self, risk_level: str) -> str:
        """Get style for risk label."""
        colors = {
            "low": "#4CAF50",
            "medium": "#FFC107",
            "high": "#F44336"
        }
        color = colors.get(risk_level, "#9E9E9E")
        return f"background-color: {color}; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;"


class SelfImproveTab(QWidget):
    """Self-Improvement tab for autonomous code updates."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.orchestrator = get_orchestrator()
        self.analysis_worker = None
        self.setup_ui()
        self.load_proposals()
    
    def setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout(self)
        
        header_label = QLabel("<h2>🔧 Self-Improvement System</h2>")
        layout.addWidget(header_label)
        
        info_label = QLabel(
            "The AI can analyze its own code and propose improvements. "
            "All changes require your approval and are backed up automatically."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        control_group = QGroupBox("Analysis Controls")
        control_layout = QHBoxLayout()
        
        self.analyze_btn = QPushButton("🔍 Analyze Code")
        self.analyze_btn.clicked.connect(self.start_analysis)
        self.analyze_btn.setStyleSheet("padding: 10px; font-size: 12pt;")
        control_layout.addWidget(self.analyze_btn)
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.load_proposals)
        control_layout.addWidget(self.refresh_btn)
        
        control_layout.addStretch()
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("padding: 8px; background-color: #E3F2FD; border-radius: 4px;")
        layout.addWidget(self.status_label)
        
        proposals_group = QGroupBox("Proposals")
        proposals_layout = QVBoxLayout()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.proposals_container = QWidget()
        self.proposals_layout = QVBoxLayout(self.proposals_container)
        self.proposals_layout.addStretch()
        
        scroll.setWidget(self.proposals_container)
        proposals_layout.addWidget(scroll)
        
        proposals_group.setLayout(proposals_layout)
        layout.addWidget(proposals_group)
    
    def start_analysis(self):
        """Start code analysis."""
        if self.analysis_worker and self.analysis_worker.isRunning():
            QMessageBox.warning(self, "Analysis Running", "Analysis is already in progress.")
            return
        
        reply = QMessageBox.question(
            self,
            "Start Analysis",
            "This will analyze your code and propose improvements. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.analyze_btn.setEnabled(False)
        self.status_label.setText("🔍 Analyzing code...")
        self.status_label.setStyleSheet("padding: 8px; background-color: #FFF9C4; border-radius: 4px;")
        
        self.analysis_worker = AnalysisWorker(max_files=5)
        self.analysis_worker.finished.connect(self.on_analysis_finished)
        self.analysis_worker.error.connect(self.on_analysis_error)
        self.analysis_worker.start()
    
    def on_analysis_finished(self, proposal_ids: list):
        """Handle analysis completion."""
        self.analyze_btn.setEnabled(True)
        
        if proposal_ids:
            self.status_label.setText(f"✅ Analysis complete! Generated {len(proposal_ids)} proposals.")
            self.status_label.setStyleSheet("padding: 8px; background-color: #C8E6C9; border-radius: 4px;")
        else:
            self.status_label.setText("ℹ️ No improvements found.")
            self.status_label.setStyleSheet("padding: 8px; background-color: #E3F2FD; border-radius: 4px;")
        
        self.load_proposals()
    
    def on_analysis_error(self, error: str):
        """Handle analysis error."""
        self.analyze_btn.setEnabled(True)
        self.status_label.setText(f"❌ Analysis failed: {error}")
        self.status_label.setStyleSheet("padding: 8px; background-color: #FFCDD2; border-radius: 4px;")
        
        QMessageBox.critical(self, "Analysis Error", f"Failed to analyze code:\n{error}")
    
    def load_proposals(self):
        """Load and display proposals."""
        try:
            while self.proposals_layout.count() > 1:  # Keep stretch
                item = self.proposals_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            pending = self.orchestrator.get_pending_proposals()
            
            history = self.orchestrator.get_proposal_history(limit=10)
            
            all_proposals = pending + [p for p in history if p not in pending]
            
            if not all_proposals:
                no_proposals_label = QLabel("No proposals yet. Click 'Analyze Code' to start.")
                no_proposals_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                no_proposals_label.setStyleSheet("color: #999; padding: 40px; font-size: 12pt;")
                self.proposals_layout.insertWidget(0, no_proposals_label)
                return
            
            for proposal_data in all_proposals:
                widget = ProposalWidget(proposal_data)
                widget.approved.connect(self.approve_proposal)
                widget.rejected.connect(self.reject_proposal)
                widget.applied.connect(self.apply_proposal)
                widget.rolled_back.connect(self.rollback_proposal)
                
                self.proposals_layout.insertWidget(self.proposals_layout.count() - 1, widget)
        
        except Exception as e:
            logger.error(f"Failed to load proposals: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load proposals:\n{e}")
    
    def approve_proposal(self, proposal_id: str):
        """Approve a proposal."""
        reply = QMessageBox.question(
            self,
            "Approve Proposal",
            f"Approve proposal {proposal_id}?\n\nThis will allow it to be applied to your code.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.orchestrator.approve_proposal(proposal_id):
                QMessageBox.information(self, "Success", "Proposal approved!")
                self.load_proposals()
            else:
                QMessageBox.critical(self, "Error", "Failed to approve proposal.")
    
    def reject_proposal(self, proposal_id: str):
        """Reject a proposal."""
        reply = QMessageBox.question(
            self,
            "Reject Proposal",
            f"Reject proposal {proposal_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.orchestrator.reject_proposal(proposal_id, reason="User rejected"):
                QMessageBox.information(self, "Success", "Proposal rejected.")
                self.load_proposals()
            else:
                QMessageBox.critical(self, "Error", "Failed to reject proposal.")
    
    def apply_proposal(self, proposal_id: str):
        """Apply an approved proposal."""
        reply = QMessageBox.warning(
            self,
            "Apply Changes",
            f"Apply proposal {proposal_id}?\n\n"
            "⚠️ This will modify your code!\n"
            "A backup will be created automatically.\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.status_label.setText(f"🚀 Applying {proposal_id}...")
            self.status_label.setStyleSheet("padding: 8px; background-color: #FFF9C4; border-radius: 4px;")
            
            if self.orchestrator.apply_proposal(proposal_id):
                QMessageBox.information(
                    self,
                    "Success",
                    "Proposal applied successfully!\n\n"
                    "A backup was created. You can rollback if needed."
                )
                self.status_label.setText("✅ Proposal applied!")
                self.status_label.setStyleSheet("padding: 8px; background-color: #C8E6C9; border-radius: 4px;")
                self.load_proposals()
            else:
                QMessageBox.critical(self, "Error", "Failed to apply proposal.")
                self.status_label.setText("❌ Failed to apply proposal")
                self.status_label.setStyleSheet("padding: 8px; background-color: #FFCDD2; border-radius: 4px;")
    
    def rollback_proposal(self, proposal_id: str):
        """Rollback an applied proposal."""
        reply = QMessageBox.warning(
            self,
            "Rollback Changes",
            f"Rollback proposal {proposal_id}?\n\n"
            "⚠️ This will restore code from the backup.\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.orchestrator.rollback_proposal(proposal_id):
                QMessageBox.information(self, "Success", "Proposal rolled back successfully!")
                self.load_proposals()
            else:
                QMessageBox.critical(self, "Error", "Failed to rollback proposal.")
