# ui_popup.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QCheckBox, QPushButton, QGroupBox, QScrollArea, QWidget)


class RenfortPopup(QDialog):
    def __init__(self, dps_info, suggestions, all_suggestions, parent=None):
        super().__init__(parent)
        self.setWindowTitle("💡 Suggestions de Renfort")
        self.setMinimumWidth(500)
        self.suggestions = suggestions          # 3 voisins recommandés
        self.all_suggestions = all_suggestions  # toutes les antennes
        self.checkboxes = {}   # antenne -> (QCheckBox, capacite)
        self.group_boxes = {}  # antenne -> QGroupBox
        self.dps_info = dps_info
        self._neighbor_antennes = {s['antenne'] for s in suggestions}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        header = QLabel(
            f"<b>DPS :</b> {self.dps_info['nom_dps']}<br>"
            f"<b>Date :</b> {self.dps_info['jour']}<br>"
            f"<b>Antenne :</b> {self.dps_info['antenne']}<br>"
            f"<b>Besoin :</b> <span style='color:red; font-weight:bold;'>"
            f"{self.dps_info['tl'] - self.dps_info['nb']} personnes</span>")
        header.setWordWrap(True)
        layout.addWidget(header)

        # Option toutes les antennes
        self.cb_toutes = QCheckBox("🌐 Afficher toutes les antennes")
        self.cb_toutes.setStyleSheet("font-weight: bold; margin: 6px 0;")
        self.cb_toutes.toggled.connect(self._toggle_all)
        layout.addWidget(self.cb_toutes)

        # Scroll avec tous les groupes construits à l'avance
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)

        for sugg in self.all_suggestions:
            gb = self._make_group(sugg)
            self.group_boxes[sugg['antenne']] = gb
            self.scroll_layout.addWidget(gb)
            # Cacher les antennes non-voisines par défaut
            if sugg['antenne'] not in self._neighbor_antennes:
                gb.setVisible(False)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        btn_layout = QHBoxLayout()
        btn_annuler = QPushButton("Annuler")
        btn_annuler.clicked.connect(self.reject)
        btn_valider = QPushButton("✅ Valider et Écrire les [R]")
        btn_valider.setStyleSheet(
            "background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        btn_valider.clicked.connect(self.accept)
        btn_layout.addWidget(btn_annuler)
        btn_layout.addWidget(btn_valider)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _make_group(self, sugg):
        est_voisin = sugg['antenne'] in self._neighbor_antennes
        titre = f"{sugg['antenne']}"
        if est_voisin:
            titre += f"  —  voisin n°{sugg['distance']}"

        gb = QGroupBox(titre)
        gb_layout = QVBoxLayout()

        info_lbl = QLabel(
            f"📊 État : {sugg['disponibilite']}\n"
            f"👥 Capacité estimée : ~{sugg['capacite']} pers.")
        info_lbl.setWordWrap(True)
        info_lbl.setStyleSheet("color: #555;")

        cb = QCheckBox("Sélectionner pour ce renfort")
        self.checkboxes[sugg['antenne']] = (cb, sugg['capacite'])

        gb_layout.addWidget(info_lbl)
        gb_layout.addWidget(cb)
        gb.setLayout(gb_layout)
        return gb

    def _toggle_all(self, checked):
        for antenne, gb in self.group_boxes.items():
            if antenne not in self._neighbor_antennes:
                gb.setVisible(checked)

    def get_selected_antennes(self):
        return [(antenne, capacite)
                for antenne, (cb, capacite) in self.checkboxes.items()
                if cb.isChecked()]
