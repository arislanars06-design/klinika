"""Patients UI subpackage."""

from clinic.ui.patients.patient_card import PatientCardDialog
from clinic.ui.patients.stats_widget import PatientStatsDialog
from clinic.ui.patients.window import PatientsWindow

__all__ = ["PatientCardDialog", "PatientStatsDialog", "PatientsWindow"]
