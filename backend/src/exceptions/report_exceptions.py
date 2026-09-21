"""レポート生成処理で使用する例外定義。"""


class ReportServiceError(Exception):
    """レポートServiceの共通エラー。"""


class ReportSourceFileNotFoundError(ReportServiceError):
    """CSV管理情報が存在しない場合のエラー。"""


class ReportPhysicalFileNotFoundError(ReportServiceError):
    """CSV実ファイルが存在しない場合のエラー。"""


class ReportAlreadyExistsError(ReportServiceError):
    """対象CSVのレポートが登録済みの場合のエラー。"""


class ReportGenerationError(ReportServiceError):
    """AIレポート生成に失敗した場合のエラー。"""


class ReportDatabaseError(ReportServiceError):
    """レポートのDB保存に失敗した場合のエラー。"""
