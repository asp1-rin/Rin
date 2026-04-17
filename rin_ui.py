import sys
import subprocess
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

class RinEngineUI(QMainWindow):
    def __init__(self):
        super().__init__()
        # Internal state for memory tracking
        self.address_list = []
        self.target_pid = None 

        self.init_window_settings()
        self.init_ui()

    def init_window_settings(self):
        """Set up the main window aesthetic and geometry."""
        self.setWindowTitle("RIN-ENGINE CONTROL PANEL v2.0")
        self.setFixedSize(800, 600)
        self.setStyleSheet("background-color: #000000; color: #FFFFFF;")

    def init_ui(self):
        """Build the UI layout based on the user's conceptual design."""
        main_layout = QVBoxLayout()
        top_layout = QHBoxLayout()
        bottom_layout = QHBoxLayout()

        # --- Top Section: Search & Location Controls ---
        # Search functionality for value filtering
        search_box = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter value to search...")
        self.search_input.returnPressed.connect(self.run_search)
        search_box.addWidget(QLabel("🔍"))
        search_box.addWidget(self.search_input)
        
        # PID input - Critical for targeting the correct process
        pid_box = QHBoxLayout()
        self.pid_input = QLineEdit()
        self.pid_input.setPlaceholderText("Target PID...")
        self.pid_input.setMaximumWidth(100)
        pid_box.addWidget(QLabel("PID:"))
        pid_box.addWidget(self.pid_input)

        # Location input for direct memory access
        location_box = QHBoxLayout()
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("hex location...")
        location_btn = QPushButton("▲")
        location_btn.clicked.connect(self.read_at_location)
        location_box.addWidget(location_btn)
        location_box.addWidget(self.location_input)

        top_layout.addLayout(search_box)
        top_layout.addLayout(pid_box)
        top_layout.addLayout(location_box)

        # --- Bottom Section: Results List & Memory Manipulation ---
        # Left Panel: Display list of found memory addresses
        self.result_list = QListWidget()
        self.result_list.setStyleSheet("background-color: #888888; color: black; border: 2px solid white;")
        self.result_list.itemClicked.connect(self.select_address)
        bottom_layout.addWidget(self.result_list, 1)

        # Right Panel: Read/Write controls
        right_panel = QVBoxLayout()
        
        self.current_val_label = QLabel("Current Value")
        self.current_val_label.setStyleSheet("background-color: #888888; padding: 20px; color: black;")
        self.current_val_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        arrow_label = QLabel("↓")
        arrow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.dump_input = QLineEdit()
        self.dump_input.setPlaceholderText("New value to dump...")
        self.dump_input.setStyleSheet("background-color: #888888; color: black; padding: 10px;")
        
        self.dump_btn = QPushButton("dump")
        self.dump_btn.clicked.connect(self.run_dump)
        
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self.reset_all)
        self.reset_btn.setMinimumHeight(100)

        right_panel.addWidget(self.current_val_label)
        right_panel.addWidget(arrow_label)
        right_panel.addWidget(self.dump_input)
        right_panel.addWidget(self.dump_btn)
        right_panel.addStretch()
        right_panel.addWidget(self.reset_btn)
        
        bottom_layout.addLayout(right_panel, 1)

        # Final layout assembly
        main_layout.addLayout(top_layout)
        main_layout.addLayout(bottom_layout)
        
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def run_search(self):
        """Execute memory scan or filter existing results."""
        val = self.search_input.text()
        pid = self.pid_input.text()
        if not val or not pid: return

        if not self.address_list:
            # Initial scan logic (To be implemented with C++ scanner)
            self.result_list.addItem(f"Starting scan for {val} in PID {pid}...")
            # Mock data for simulation
            self.address_list = ["0x7B123456", "0x7B1234F0", "0x7B1235A0"]
        else:
            # Filtering mode: Re-read values of previously found addresses
            self.result_list.clear()
            new_list = []
            for addr in self.address_list:
                current_val = self.call_engine("r", addr)
                if current_val == val:
                    new_list.append(addr)
                    self.result_list.addItem(addr)
            self.address_list = new_list

    def read_at_location(self):
        """Fetch and display value from a specific memory address."""
        addr = self.location_input.text()
        if addr:
            val = self.call_engine("r", addr)
            self.current_val_label.setText(f"Value: {val}")

    def run_dump(self):
        """Inject new value into the targeted memory address."""
        addr = self.location_input.text()
        val = self.dump_input.text()
        if addr and val:
            self.call_engine("w", addr, val)
            self.current_val_label.setText(f"Dumped: {val}")

    def reset_all(self):
        """Clear all session data and UI fields."""
        self.address_list = []
        self.result_list.clear()
        self.search_input.clear()
        self.location_input.clear()
        self.current_val_label.setText("Engine Reset")

    def call_engine(self, mode, addr, val=""):
        """Interface between Python UI and C++ RIN-ENGINE."""
        pid = self.pid_input.text()
        cmd = ["./rin-engine", mode, pid, addr]
        if val: cmd.append(val)
        
        try:
            # Execute binary and capture standard output
            result = subprocess.check_output(cmd).decode()
            return result.split("=>")[-1].strip()
        except Exception as e:
            return f"Error: {str(e)}"

    def select_address(self, item):
        """Auto-populate the location field when an item is selected."""
        self.location_input.setText(item.text())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RinEngineUI()
    window.show()
    sys.exit(app.exec())
