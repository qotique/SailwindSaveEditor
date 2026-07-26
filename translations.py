import abc

class MetaAbstractString(abc.ABCMeta):
    def __getitem__(cls, language: str) -> str:
        # cls — это сам класс (например, MainTitle)
        if language in cls.translations:
            return cls.translations[language]
        return "Missing translation"

class AbstractString(metaclass=MetaAbstractString):
    translations: dict[str, str]


class Strings:
    class MainTitle(AbstractString):
        translations: dict[str, str] = {
            "English": "Sailwind Save Editor",
            "Русский": "Редактор сохранений Sailwind",
        }

    class SettingsTitle(AbstractString):
        translations: dict[str, str] = {
            "English": "Settings",
            "Русский": "Настройки",
        }

    class OpenSettings(AbstractString):
        translations: dict[str, str] = {
            "English": "Open settings",
            "Русский": "Открыть настройки",
        }

    class SafeToEdit(AbstractString):
        translations: dict[str, str] = {
            "English": "Only safe fields",
            "Русский": "Только безопасные поля",
        }

    class SafeToEditDescription(AbstractString):
        translations: dict[str, str] = {
            "English": "Show only safe to edit fields",
            "Русский": "Показывать только безопасные для редактирования поля",
        }

    class ChooseTheme(AbstractString):
        translations: dict[str, str] = {
            "English": "Theme",
            "Русский": "Оформление",
        }

    class ChooseLanguage(AbstractString):
        translations: dict[str, str] = {
            "English": "Language",
            "Русский": "Язык",
        }

    class CheckUpdates(AbstractString):
        translations: dict[str, str] = {
            "English": "Check updates on startup",
            "Русский": "Проверять обновления при запуске",
        }

    class NoFileSelected(AbstractString):
        translations: dict[str, str] = {
            "English": "No file selected",
            "Русский": "Файл не выбран",
        }

    class OpenSaveFile(AbstractString):
        translations: dict[str, str] = {
            "English": "Open save file",
            "Русский": "Открыть файл сохранения",
        }

    class SelectSaveFile(AbstractString):
        translations: dict[str, str] = {
            "English": "Select Sailwind save file",
            "Русский": "Выбрать файл сохранения Sailwind",
        }

    class SaveFile(AbstractString):
        translations: dict[str, str] = {
            "English": "Save",
            "Русский": "Сохранить",
        }

    class ImportJSON(AbstractString):
        translations: dict[str, str] = {
            "English": "Import JSON",
            "Русский": "Импортировать JSON",
        }
    
    class ExportJSON(AbstractString):
        translations: dict[str, str] = {
            "English": "Export JSON",
            "Русский": "Экспортировать JSON",
        }

    class LanguageNotSupportedYetTitle(AbstractString):
        translations: dict[str, str] = {
            "English": " is not supported yet",
            "Русский": " еще не поддерживается",
        }

    class LanguageNotSupportedYetDescription(AbstractString):
        translations: dict[str, str] = {
            "English": "Please wait for updates",
            "Русский": "Пожалуйста, дождитесь обновления",
        }

    class Dismiss(AbstractString):
        translations: dict[str, str] = {
            "English": "Dismiss",
            "Русский": "Отменить",
        }

    class NoReleaseNotesProvided(AbstractString):
        translations: dict[str, str] = {
            "English": "No release notes provided with this release\n"
                       "See the release page on GitHub for details",
            "Русский": "Список изменений не представлен в этом обновлении\n"
                       "Для подробностей посетите страницу обновления на GitHub",
        }

    class CurrentVersion(AbstractString):
        translations: dict[str, str] = {
            "English": "Current version",
            "Русский": "Текущая версия",
        }

    class LatestVersion(AbstractString):
        translations: dict[str, str] = {
            "English": "Latest version",
            "Русский": "Последняя версия",
        }
    
    class Download(AbstractString):
        translations: dict[str, str] = {
            "English": "Download",
            "Русский": "Загрузить",
        }

    class CheckFailed(AbstractString):
        translations: dict[str, str] = {
            "English": "Check failed",
            "Русский": "Проверка не удалась",
        }
