import sys
import subprocess
import os
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

class RinEngineUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.address_list = []
        self.engine_path = "./rin-engine"
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("RIN-ENGINE CONTROL PANEL v3.0")
        self.setFixedSize(800, 600)
        self.setStyleSheet("background-color: #000000; color: #FFFFFF;")

        main_layout = QVBoxLayout()
        top_layout = QHBoxLayout()
        bottom_layout = QHBoxLayout()

        # Search Bar
        search_box = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Value to scan...")
        self.search_input.returnPressed.connect(self.run_search)
        search_box.addWidget(QLabel("🔍"))
        search_box.addWidget(self.search_input)
        
        # PID Input
        pid_box = QHBoxLayout()
        self.pid_input = QLineEdit()
        self.pid_input.setPlaceholderText("PID...")
        self.pid_input.setMaximumWidth(80)
        pid_box.addWidget(QLabel("PID:"))
        pid_box.addWidget(self.pid_input)

        # Location / Address Bar
        location_box = QHBoxLayout()
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Address...")
        location_btn = QPushButton("▲")
        location_btn.clicked.connect(self.read_at_location)
        location_box.addWidget(location_btn)
        location_box.addWidget(self.location_input)

        top_layout.addLayout(search_box)
        top_layout.addLayout(pid_box)
        top_layout.addLayout(location_box)

        # Result List (Left)
        self.result_list = QListWidget()
        self.result_list.setStyleSheet("background-color: #222222; color: #00FF00; border: 1px solid #555;")
        self.result_list.itemClicked.connect(self.select_address)
        bottom_layout.addWidget(self.result_list, 1)

        # Right Controls
        right_panel = QVBoxLayout()
        self.current_val_label = QLabel("VALUE")
        self.current_val_label.setStyleSheet("background-color: #333333; padding: 20px; font-size: 18px;")
        self.current_val_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.dump_input = QLineEdit()
        self.dump_input.setPlaceholderText("New value...")
        self.dump_input.setStyleSheet("background-color: #333333; padding: 10px; border: none;")
        
        self.dump_btn = QPushButton("DUMP")
        self.dump_btn.clicked.connect(self.run_dump)
        self.dump_btn.setStyleSheet("background-color: #444; padding: 10px;")
        
        self.reset_btn = QPushButton("RESET")
        self.reset_btn.clicked.connect(self.reset_all)
        self.reset_btn.setMinimumHeight(80)

        right_panel.addWidget(self.current_val_label)
        right_panel.addWidget(QLabel("↓", alignment=Qt.AlignmentFlag.AlignCenter))
        right_panel.addWidget(self.dump_input)
        right_panel.addWidget(self.dump_btn)
        right_panel.addStretch()
        right_panel.addWidget(self.reset_btn)
        
        bottom_layout.addLayout(right_panel, 1)
        main_layout.addLayout(top_layout)
        main_layout.addLayout(bottom_layout)
        
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def call_engine(self, mode, target, val=""):
        pid = self.pid_input.text()
        if not pid: return "ERR_NO_PID"
        
        cmd = [self.engine_path, mode, pid, target]
        if val: cmd.append(val)
        
        try:
            # Capture stdout and handle as string
            res = subprocess.check_output(cmd).decode()
            return res
        except:
            return "ERR_EXEC"

    def run_search(self):
        """Unified Scan & Filter Logic"""
        val = self.search_input.text()
        if not val: return

        self.result_list.clear()
        
        if not self.address_list:
            # FIRST SCAN: Search entire memory (Mode 's')
            output = self.call_engine("s", val)
            # Parse 'MATCH => 0x...' lines
            matches = [line.split("=>")[-1].strip() for line in output.splitlines() if "MATCH" in line]
            self.address_list = matches
            for addr in self.address_list:
                self.result_list.addItem(addr)
        else:
            # FILTER SCAN: Re-check existing addresses (Mode 'r')
            new_list = []
            for addr in self.address_list:
                res = self.call_engine("r", addr)
                if "=>" in res and res.split("=>")[-1].strip() == val:
                    new_list.append(addr)
                    self.result_list.addItem(addr)
            self.address_list = new_list

    def read_at_location(self):
        addr = self.location_input.text()
        if addr:
            res = self.call_engine("r", addr)
            val = res.split("=>")[-1].strip() if "=>" in res else "Error"
            self.current_val_label.setText(val)

    def run_dump(self):
        addr = self.location_input.text()
        val = self.dump_input.text()
        if addr and val:
            self.call_engine("w", addr, val)
            self.current_val_label.setText(f"SET: {val}")

    def reset_all(self):
        self.address_list = []
        self.result_list.clear()
        self.search_input.clear()
        self.location_input.clear()
        self.current_val_label.setText("RESET")

    def select_address(self, item):
        self.location_input.setText(item.text())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RinEngineUI()
    window.show()
    sys.exit(app.exec())
