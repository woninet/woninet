from pydantic import ValidationError
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError
from woninet.database.base import Base
from woninet.settings import get_settings
from woninet.exc import DatabaseConnectionFailed
from woninet.core.diagnostic import DiagnosticManager


class DatabaseEngine:
    """
    Encapsulate database engine creation and initialization logic, and manage
    common database errors.

    Attributes:
        database_type (str): The database type (PostgreSQL, or SQLite).
        database_path (str): Location to the database (Path for SQLite,
            or connection URL for PostgreSQL).
        diagnostics (DiagnosticManager): Instance of DiagnosticManager to collect database's
            issues.
    """

    def __init__(
        self,
        database_type: str,
        database_path: str | None,
        diagnostics: DiagnosticManager,
    ) -> None:
        """
        Create a SQLAlchemy engine and session factory for the given database.

        Args:
            database_type (str): The database type (PostgreSQL, or SQLite)
            database_path (str): Location to the database (Path for SQLite,
                or connection URL for PostgreSQL).
            diagnostics (DiagnosticManager): Instance of DiagnosticManager to collect database's
                issues.
        """
        self.database_type: str = database_type
        self.database_path: str = database_path
        self.diagnostics = diagnostics
        self.woninet_database_url: str | None = None

        self._validate_database_params()

        if self.database_type.lower() == "sqlite":
            self.engine = create_engine(
                f"sqlite:///{self.database_path}", echo=False, future=True
            )
        elif self.database_type.lower() == "postgresql":
            self.engine = create_engine(self.woninet_database_url, echo=False)
        else:
            self.diagnostics.add_issue(
                component="database",
                code="DATABASE_ENGINE_FAILED",
                message="Cannot create the database engine.",
            )
            self.diagnostics.add_issue(
                component="configuration",
                code="WRONG_CONFIG_KEY",
                message="The provided `database_type` in the `config.json` is not valid. Use either `sqlite` or `postgresql`.",
            )
            raise ValueError(
                "The provided `database_type` in the `config.json` is not valid. Use either `sqlite` or `postgresql`."
            )

        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False)

    def init_db(self) -> None:
        """
        Initialize the database and create missing tables.
        """
        try:
            import woninet.database.tables  # noqa: F401

            Base.metadata.create_all(bind=self.engine)
        except OperationalError:
            host = self.engine.url.host
            port = self.engine.url.port
            self.diagnostics.add_issue(
                component="database",
                code="DATABASE_CONNECTION_FAILED",
                message=f"Connection failed. Could not connect to database at {host}:{port}",
            )
            raise DatabaseConnectionFailed(
                f"Could not connect to database at {host}:{port}"
            )

    def get_database_engine(self) -> Engine:
        """
        Return the SQLAlchemy Engine instance.
        """
        return self.engine

    def get_session_factory(self) -> sessionmaker[Session]:
        """
        Return the SQLAlchemy session factory used to create sessions.
        """
        return self.SessionLocal

    def _validate_database_params(self) -> None:
        """
        Validate the database parameters such as database_type and
        database_path, and handle common SQLAlchemy and Pydantic errors.
        """
        if self.database_type is None:
            self.diagnostics.add_issue(
                component="database",
                code="DATABASE_CONFIG_FAILED",
                message="Cannot validate the database parameters form `config.json`.",
            )
            self.diagnostics.add_issue(
                component="configuration",
                code="CONFIG_KEY_MISSING",
                message="Missing required key 'type' under 'database' in 'config.json'.",
            )
            raise KeyError(
                "Missing required key 'type' under 'database' in 'config.json'."
            )

        if self.database_type == "sqlite":
            if self.database_path is None or self.database_path.strip() == "":
                self.diagnostics.add_issue(
                    component="database",
                    code="DATABASE_CONFIG_FAILED",
                    message="Cannot validate the database parameters form `config.json`.",
                )
                self.diagnostics.add_issue(
                    component="configuration",
                    code="CONFIG_KEY_MISSING",
                    message="The database URL or path is not defined.",
                )
                raise ValueError("The database URL or path is not defined.")

        try:
            settings = get_settings()
            self.woninet_database_url = settings.woninet_database_url
        except ValidationError:
            self.woninet_database_url = self.database_path

        if self.woninet_database_url is None:
            self.diagnostics.add_issue(
                component="database",
                code="DATABASE_CONFIG_FAILED",
                message="Cannot validate the database parameters form `config.json`.",
            )
            self.diagnostics.add_issue(
                component="configuration",
                code="CONFIG_KEY_MISSING",
                message="The database URL or path is not defined.",
            )
            raise ValueError("The database URL or path is not defined.")
