from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Literal


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    database_url: str = "sqlite:///./compliancewatch.db"
    regulations_gov_api_key: str = ""
    sendgrid_api_key: str = ""
    sendgrid_from_email: str = "alerts@compliancewatch.app"
    sendgrid_from_name: str = "ComplianceWatch"
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    app_env: Literal["development", "production"] = "development"
    log_level: str = "INFO"
    ingest_lookback_days: int = 1

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()

CLAUDE_MODEL = "claude-opus-4-8"

TRACKED_AGENCIES = [
    "occupational-safety-and-health-administration",
    "food-and-drug-administration",
    "federal-trade-commission",
    "labor-department",
    "wage-and-hour-division",
    "environmental-protection-agency",
    "small-business-administration",
    "equal-employment-opportunity-commission",
    "national-labor-relations-board",
    "internal-revenue-service",
    "financial-crimes-enforcement-network",
    "food-safety-and-inspection-service",
    "federal-communications-commission",
    "consumer-product-safety-commission",
    "federal-motor-carrier-safety-administration",
]

INDUSTRIES = [
    "restaurant_food_service",
    "food_manufacturing",
    "retail",
    "construction",
    "manufacturing",
    "healthcare",
    "transportation",
    "agriculture",
    "finance_insurance",
    "childcare",
    "personal_services",
    "auto_repair",
    "hospitality_lodging",
    "real_estate",
    "all_businesses",
]
