from sqlalchemy.orm import Session

from app.models import SystemSetting


class SystemSettingRepository:
    def __init__(self, db: Session):
        self.db = db

    def all(self) -> dict[str, str]:
        settings = self.db.query(SystemSetting).all()
        return {setting.key: setting.value for setting in settings}

    def set_many(self, values: dict[str, str]) -> None:
        for key, value in values.items():
            setting = self.db.get(SystemSetting, key)
            if setting is None:
                setting = SystemSetting(key=key, value=value)
                self.db.add(setting)
            else:
                setting.value = value
        self.db.flush()
