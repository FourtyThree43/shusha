"""
Application Bootstrap and Composition Root for Shusha 2.
"""

import contextlib
import logging
from pathlib import Path

from platformdirs import user_config_dir, user_data_dir

from shusha.application.services.sync_coordinator import SyncCoordinator
from shusha.application.use_cases.category_use_cases import (
    AssignCategoryUseCase,
    CreateCategoryUseCase,
    DeleteCategoryUseCase,
    UpdateCategoryUseCase,
)
from shusha.application.use_cases.download_use_cases import (
    AddDownloadUseCase,
    ChangeDownloadOptionsUseCase,
    InspectDownloadUseCase,
    PauseDownloadUseCase,
    RemoveDownloadUseCase,
    ResumeDownloadUseCase,
)
from shusha.application.use_cases.queue_use_cases import (
    ReorderQueueUseCase,
    SetQueueLimitsUseCase,
)
from shusha.infrastructure.aria2.client import Aria2Client
from shusha.infrastructure.aria2.jsonrpc import JsonRpcTransport
from shusha.infrastructure.aria2.option_registry import OptionRegistry
from shusha.infrastructure.aria2.ws_client import Aria2WebSocketClient
from shusha.infrastructure.configuration.settings_store import SettingsStore
from shusha.infrastructure.daemon.config import DaemonConfig
from shusha.infrastructure.daemon.manager import DaemonSupervisor
from shusha.infrastructure.persistence.database import DatabaseManager
from shusha.infrastructure.persistence.repositories.category_repository import (
    CategoryRepository,
)
from shusha.infrastructure.persistence.repositories.download_repository import (
    DownloadRepository,
)
from shusha.presentation.app_context import AppContext
from shusha.security.secrets import SecretStore

logger = logging.getLogger("shusha")


def setup_logging(debug: bool = False) -> None:
    """Configure structured console and file logging."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def build_app_context(
    data_dir: Path | None = None,
    config_dir: Path | None = None,
) -> AppContext:
    """Compose and wire all architectural components into an AppContext DI container."""
    if data_dir is None:
        data_dir = Path(user_data_dir("shusha", "Shusha"))
    if config_dir is None:
        config_dir = Path(user_config_dir("shusha", "Shusha"))

    data_dir.mkdir(parents=True, exist_ok=True)
    config_dir.mkdir(parents=True, exist_ok=True)

    # 1. Persistence & Secrets
    db_path = data_dir / "shusha.db"
    db_manager = DatabaseManager(db_path)
    download_repo = DownloadRepository(db_manager)
    category_repo = CategoryRepository(db_manager)
    settings_store = SettingsStore(db_manager)

    secrets_path = config_dir / "secrets.json"
    secret_store = SecretStore(secrets_path)
    rpc_secret = secret_store.get_or_generate_rpc_secret()

    # Load preferences
    settings = settings_store.load_settings()

    # 2. aria2 RPC Client
    rpc_endpoint = f"http://{settings.aria2_host}:{settings.aria2_port}/jsonrpc"
    transport = JsonRpcTransport(endpoint=rpc_endpoint, secret=rpc_secret)
    registry = OptionRegistry.get_default_registry()
    client = Aria2Client(transport=transport, registry=registry)

    # 3. WebSocket Event Client
    ws_endpoint = f"ws://{settings.aria2_host}:{settings.aria2_port}/jsonrpc"
    ws_client = Aria2WebSocketClient(endpoint=ws_endpoint, secret=rpc_secret)

    # 4. Daemon Supervisor
    daemon_conf = DaemonConfig(
        host=settings.aria2_host,
        port=settings.aria2_port,
        secret=rpc_secret,
        download_dir=Path(settings.download_dir),
        session_file=data_dir / "aria2.session",
        input_file=data_dir / "aria2.session",
        log_file=data_dir / "aria2.log",
        max_concurrent_downloads=settings.max_active_downloads,
    )
    pid_file = data_dir / "aria2.pid"
    custom_exe = (
        Path(settings.custom_aria2_path) if settings.custom_aria2_path else None
    )
    daemon_supervisor = DaemonSupervisor(
        config=daemon_conf, custom_executable=custom_exe, pid_file=pid_file
    )

    # 5. Background State Synchronizer
    sync_coordinator = SyncCoordinator(
        client=client,
        download_repo=download_repo,
        ws_client=ws_client,
        poll_interval=1.0,
    )

    # 6. Application Use Cases
    add_download_uc = AddDownloadUseCase(
        client=client,
        download_repo=download_repo,
        category_repo=category_repo,
        default_dir=Path(settings.download_dir),
    )
    pause_download_uc = PauseDownloadUseCase(client=client, download_repo=download_repo)
    resume_download_uc = ResumeDownloadUseCase(
        client=client, download_repo=download_repo
    )
    remove_download_uc = RemoveDownloadUseCase(
        client=client, download_repo=download_repo
    )
    inspect_download_uc = InspectDownloadUseCase(
        client=client, download_repo=download_repo
    )
    change_options_uc = ChangeDownloadOptionsUseCase(
        client=client, download_repo=download_repo
    )

    create_category_uc = CreateCategoryUseCase(category_repo=category_repo)
    update_category_uc = UpdateCategoryUseCase(category_repo=category_repo)
    delete_category_uc = DeleteCategoryUseCase(category_repo=category_repo)
    assign_category_uc = AssignCategoryUseCase(
        download_repo=download_repo, category_repo=category_repo
    )

    reorder_queue_uc = ReorderQueueUseCase(client=client, download_repo=download_repo)
    set_queue_limits_uc = SetQueueLimitsUseCase(client=client)

    return AppContext(
        client=client,
        daemon_supervisor=daemon_supervisor,
        download_repo=download_repo,
        category_repo=category_repo,
        settings_store=settings_store,
        sync_coordinator=sync_coordinator,
        add_download_uc=add_download_uc,
        pause_download_uc=pause_download_uc,
        resume_download_uc=resume_download_uc,
        remove_download_uc=remove_download_uc,
        inspect_download_uc=inspect_download_uc,
        change_options_uc=change_options_uc,
        create_category_uc=create_category_uc,
        update_category_uc=update_category_uc,
        delete_category_uc=delete_category_uc,
        assign_category_uc=assign_category_uc,
        reorder_queue_uc=reorder_queue_uc,
        set_queue_limits_uc=set_queue_limits_uc,
    )


def run_gui(ctx: AppContext | None = None) -> None:
    """Launch the primary desktop GUI application."""
    from shusha.presentation.views.main_window import MainWindow

    if ctx is None:
        ctx = build_app_context()

    settings = ctx.settings_store.load_settings()

    # Start managed local daemon if auto-start is enabled
    if settings.auto_start_daemon:
        logger.info("Ensuring aria2c daemon is running...")
        ctx.daemon_supervisor.start()

    # Start sync coordinator
    ctx.sync_coordinator.start()

    # Create & run main window
    app = MainWindow(ctx)
    try:
        app.mainloop()
    finally:
        logger.info("Shutting down Shusha application...")
        ctx.sync_coordinator.stop()
        with contextlib.suppress(Exception):
            ctx.client.save_session()
