from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Language:
    """A supported language."""
    code: str  # ISO 639-1
    name: str
    native_name: str
    direction: str = "ltr"  # ltr or rtl


@dataclass
class Translation:
    """A translation entry."""
    key: str
    language: str
    value: str
    context: str = ""


# Supported languages
SUPPORTED_LANGUAGES = {
    "en": Language(code="en", name="English", native_name="English"),
    "es": Language(code="es", name="Spanish", native_name="Español"),
    "fr": Language(code="fr", name="French", native_name="Français"),
    "de": Language(code="de", name="German", native_name="Deutsch"),
    "zh": Language(code="zh", name="Chinese", native_name="中文"),
    "ja": Language(code="ja", name="Japanese", native_name="日本語"),
    "ko": Language(code="ko", name="Korean", native_name="한국어"),
    "pt": Language(code="pt", name="Portuguese", native_name="Português"),
    "ar": Language(code="ar", name="Arabic", native_name="العربية", direction="rtl"),
    "hi": Language(code="hi", name="Hindi", native_name="हिन्दी"),
}

# Translation database
TRANSLATIONS: dict[str, dict[str, str]] = {
    # UI Labels
    "app.title": {
        "en": "AEGIS — Agentic Clinical Intelligence",
        "es": "AEGIS — Inteligencia Clínica Agéntica",
        "fr": "AEGIS — Intelligence Clinique Agentique",
        "de": "AEGIS — Agentische Klinische Intelligenz",
        "zh": "AEGIS — 代理临床智能",
        "ja": "AEGIS — エージェント臨床インテリジェンス",
    },
    "app.description": {
        "en": "Synthetic patient record investigation environment",
        "es": "Entorno de investigación de registros de pacientes sintéticos",
        "fr": "Environnement d'investigation de dossiers patients synthétiques",
        "de": "Synthetische Patientenakten-Untersuchungsumgebung",
        "zh": "合成患者记录调查环境",
        "ja": "合成患者記録調査環境",
    },

    # Investigation Labels
    "investigation.patient_id": {
        "en": "Patient ID",
        "es": "ID del Paciente",
        "fr": "ID du Patient",
        "de": "Patienten-ID",
        "zh": "患者ID",
        "ja": "患者ID",
    },
    "investigation.question": {
        "en": "Investigation Question",
        "es": "Pregunta de Investigación",
        "fr": "Question d'Investigation",
        "de": "Untersuchungsfrage",
        "zh": "调查问题",
        "ja": "調査質問",
    },
    "investigation.submit": {
        "en": "Run Investigation",
        "es": "Ejecutar Investigación",
        "fr": "Lancer l'Investigation",
        "de": "Untersuchung Starten",
        "zh": "运行调查",
        "ja": "調査を実行",
    },
    "investigation.results": {
        "en": "Investigation Results",
        "es": "Resultados de la Investigación",
        "fr": "Résultats de l'Investigation",
        "de": "Untersuchungsergebnisse",
        "zh": "调查结果",
        "ja": "調査結果",
    },

    # Agent Labels
    "agent.timeline": {
        "en": "Timeline Agent",
        "es": "Agente de Línea de Tiempo",
        "fr": "Agent Chronologique",
        "de": "Zeitachsen-Agent",
        "zh": "时间线代理",
        "ja": "タイムラインエージェント",
    },
    "agent.medication": {
        "en": "Medication Agent",
        "es": "Agente de Medicamentos",
        "fr": "Agent Médicaments",
        "de": "Medikamenten-Agent",
        "zh": "药物代理",
        "ja": "医薬品エージェント",
    },
    "agent.evidence": {
        "en": "Evidence Agent",
        "es": "Agente de Evidencia",
        "fr": "Agent de Preuves",
        "de": "Beweis-Agent",
        "zh": "证据代理",
        "ja": "エビデンスエージェント",
    },
    "agent.critic": {
        "en": "Critic Agent",
        "es": "Agente Crítico",
        "fr": "Agent Critique",
        "de": "Kritik-Agent",
        "zh": "评论代理",
        "ja": "批評エージェント",
    },

    # Status Labels
    "status.completed": {
        "en": "Completed",
        "es": "Completado",
        "fr": "Terminé",
        "de": "Abgeschlossen",
        "zh": "已完成",
        "ja": "完了",
    },
    "status.pending": {
        "en": "Pending",
        "es": "Pendiente",
        "fr": "En attente",
        "de": "Ausstehend",
        "zh": "待处理",
        "ja": "保留中",
    },
    "status.failed": {
        "en": "Failed",
        "es": "Fallido",
        "fr": "Échoué",
        "de": "Fehlgeschlagen",
        "zh": "失败",
        "ja": "失敗",
    },

    # Review Labels
    "review.required": {
        "en": "Review Required",
        "es": "Revisión Requerida",
        "fr": "Révision Requise",
        "de": "Überprüfung Erforderlich",
        "zh": "需要审查",
        "ja": "レビューが必要",
    },
    "review.approved": {
        "en": "Approved",
        "es": "Aprobado",
        "fr": "Approuvé",
        "de": "Genehmigt",
        "zh": "已批准",
        "ja": "承認済み",
    },
    "review.rejected": {
        "en": "Rejected",
        "es": "Rechazado",
        "fr": "Rejeté",
        "de": "Abgelehnt",
        "zh": "已拒绝",
        "ja": "却下",
    },

    # Medical Terms
    "condition.diabetes": {
        "en": "Diabetes",
        "es": "Diabetes",
        "fr": "Diabète",
        "de": "Diabetes",
        "zh": "糖尿病",
        "ja": "糖尿病",
    },
    "condition.hypertension": {
        "en": "Hypertension",
        "es": "Hipertensión",
        "fr": "Hypertension",
        "de": "Bluthochdruck",
        "zh": "高血压",
        "ja": "高血圧",
    },
    "condition.heart_failure": {
        "en": "Heart Failure",
        "es": "Insuficiencia Cardíaca",
        "fr": "Insuffisance Cardiaque",
        "de": "Herzinsuffizienz",
        "zh": "心力衰竭",
        "ja": "心不全",
    },

    # Risk Levels
    "risk.low": {
        "en": "Low Risk",
        "es": "Riesgo Bajo",
        "fr": "Risque Faible",
        "de": "Geringes Risiko",
        "zh": "低风险",
        "ja": "低リスク",
    },
    "risk.moderate": {
        "en": "Moderate Risk",
        "es": "Riesgo Moderado",
        "fr": "Risque Modéré",
        "de": "Mäßiges Risiko",
        "zh": "中等风险",
        "ja": "中リスク",
    },
    "risk.high": {
        "en": "High Risk",
        "es": "Riesgo Alto",
        "fr": "Risque Élevé",
        "de": "Hohes Risiko",
        "zh": "高风险",
        "ja": "高リスク",
    },
    "risk.very_high": {
        "en": "Very High Risk",
        "es": "Riesgo Muy Alto",
        "fr": "Risque Très Élevé",
        "de": "Sehr Hohes Risiko",
        "zh": "极高风险",
        "ja": "非常に高いリスク",
    },

    # Error Messages
    "error.patient_not_found": {
        "en": "Patient not found",
        "es": "Paciente no encontrado",
        "fr": "Patient non trouvé",
        "de": "Patient nicht gefunden",
        "zh": "未找到患者",
        "ja": "患者が見つかりません",
    },
    "error.investigation_failed": {
        "en": "Investigation failed",
        "es": "Investigación fallida",
        "fr": "Investigation échouée",
        "de": "Untersuchung fehlgeschlagen",
        "zh": "调查失败",
        "ja": "調査に失敗しました",
    },
}


class TranslationManager:
    """Manager for translations and localization."""

    def __init__(self, default_language: str = "en"):
        self.default_language = default_language
        self.current_language = default_language
        self.translations = TRANSLATIONS

    def set_language(self, language_code: str) -> bool:
        """Set the current language."""
        if language_code in SUPPORTED_LANGUAGES:
            self.current_language = language_code
            return True
        return False

    def get(self, key: str, language: str | None = None) -> str:
        """Get a translation for a key."""
        lang = language or self.current_language

        if key in self.translations:
            if lang in self.translations[key]:
                return self.translations[key][lang]
            # Fallback to default language
            if self.default_language in self.translations[key]:
                return self.translations[key][self.default_language]

        # Return key if no translation found
        return key

    def get_supported_languages(self) -> list[dict[str, str]]:
        """Get list of supported languages."""
        return [
            {
                "code": lang.code,
                "name": lang.name,
                "native_name": lang.native_name,
                "direction": lang.direction,
            }
            for lang in SUPPORTED_LANGUAGES.values()
        ]

    def translate_dict(self, data: dict[str, Any], language: str | None = None) -> dict[str, Any]:
        """Translate string values in a dictionary."""
        translated = {}
        for key, value in data.items():
            if isinstance(value, str) and key in self.translations:
                translated[key] = self.get(key, language)
            else:
                translated[key] = value
        return translated


class GlobalHealthContext:
    """Context for global health considerations."""

    # Regional disease prevalence
    REGIONAL_DISEASES = {
        "north_america": ["diabetes", "heart_disease", "obesity", "cancer"],
        "europe": ["heart_disease", "cancer", "respiratory", "mental_health"],
        "asia": ["diabetes", "tuberculosis", "hepatitis", "respiratory"],
        "africa": ["hiv", "malaria", "tuberculosis", "malnutrition"],
        "south_america": ["dengue", "zika", "chagas", "respiratory"],
    }

    # Regional treatment guidelines
    REGIONAL_GUIDELINES = {
        "us": {"authority": "FDA", "guidelines": "US Clinical Guidelines"},
        "eu": {"authority": "EMA", "guidelines": "European Guidelines"},
        "uk": {"authority": "NICE", "guidelines": "NICE Guidelines"},
        "jp": {"authority": "PMDA", "guidelines": "Japanese Guidelines"},
        "cn": {"authority": "NMPA", "guidelines": "Chinese Guidelines"},
    }

    def get_regional_diseases(self, region: str) -> list[str]:
        """Get common diseases for a region."""
        return self.REGIONAL_DISEASES.get(region, [])

    def get_regional_guidelines(self, country: str) -> dict[str, str]:
        """Get treatment guidelines for a country."""
        return self.REGIONAL_GUIDELINES.get(country, {})

    def assess_global_health_risk(self, conditions: list[str], region: str) -> dict[str, Any]:
        """Assess health risks based on regional context."""
        regional_diseases = self.get_regional_diseases(region)
        matching_conditions = [c for c in conditions if any(d in c.lower() for d in regional_diseases)]

        return {
            "region": region,
            "regional_diseases": regional_diseases,
            "matching_conditions": matching_conditions,
            "risk_level": "high" if matching_conditions else "moderate",
            "recommendations": self._get_recommendations(matching_conditions, region),
        }

    def _get_recommendations(self, conditions: list[str], region: str) -> list[str]:
        """Get recommendations based on conditions and region."""
        recommendations = []

        if conditions:
            guidelines = self.get_regional_guidelines(region)
            if guidelines:
                recommendations.append(f"Follow {guidelines.get('guidelines', 'local')} guidelines")

            recommendations.append("Consider regional disease prevalence")
            recommendations.append("Consult local specialists")

        return recommendations


class LocalizationManager:
    """Manager for localization of dates, numbers, and units."""

    # Date formats by locale
    DATE_FORMATS = {
        "en": "MM/DD/YYYY",
        "es": "DD/MM/YYYY",
        "fr": "DD/MM/YYYY",
        "de": "DD.MM.YYYY",
        "zh": "YYYY-MM-DD",
        "ja": "YYYY年MM月DD日",
    }

    # Number formats by locale
    NUMBER_FORMATS = {
        "en": {"decimal": ".", "thousands": ","},
        "es": {"decimal": ",", "thousands": "."},
        "fr": {"decimal": ",", "thousands": " "},
        "de": {"decimal": ",", "thousands": "."},
        "zh": {"decimal": ".", "thousands": ","},
        "ja": {"decimal": ".", "thousands": ","},
    }

    # Unit systems
    UNIT_SYSTEMS = {
        "imperial": {
            "weight": "lbs",
            "height": "in",
            "temperature": "F",
            "distance": "mi",
        },
        "metric": {
            "weight": "kg",
            "height": "cm",
            "temperature": "C",
            "distance": "km",
        },
    }

    def format_date(self, date_str: str, locale: str = "en") -> str:
        """Format a date string according to locale."""
        # Simplified implementation
        return date_str

    def format_number(self, number: float, locale: str = "en") -> str:
        """Format a number according to locale."""
        fmt = self.NUMBER_FORMATS.get(locale, self.NUMBER_FORMATS["en"])
        integer_part = int(number)
        decimal_part = number - integer_part

        # Format integer part with thousands separator
        integer_str = f"{integer_part:,}".replace(",", fmt["thousands"])

        # Format decimal part
        if decimal_part:
            decimal_str = f"{decimal_part:.2f}"[1:]  # Remove leading 0
            decimal_str = decimal_str.replace(".", fmt["decimal"])
            return f"{integer_str}{decimal_str}"

        return integer_str

    def convert_temperature(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert temperature between units."""
        if from_unit == to_unit:
            return value

        if from_unit == "F" and to_unit == "C":
            return (value - 32) * 5 / 9
        elif from_unit == "C" and to_unit == "F":
            return value * 9 / 5 + 32

        return value

    def convert_weight(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert weight between units."""
        if from_unit == to_unit:
            return value

        if from_unit == "lbs" and to_unit == "kg":
            return value * 0.453592
        elif from_unit == "kg" and to_unit == "lbs":
            return value * 2.20462

        return value
