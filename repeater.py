import os
from .config import env, directory_path
from .ftp_sync import FTPManager
from .file_utils import FileManager
from .logger import LoggerSetup


def main():
    press_name = env["PRESS_NAME"]
    logger_setup = LoggerSetup(press_name)
    logger = logger_setup.logger
    logger.info(f"Start {press_name} Repeater")

    file_manager = FileManager(press_name)

    need_sync_press = ["mk", "fn"]
    if press_name in need_sync_press:
        ftp_manager = FTPManager(press_name, file_manager)
        ftp_manager.sync_press()

    process_result = file_manager.process_files()
    process_directory = os.path.join(os.getcwd(), "process_files")
    remove_result = file_manager.remove_old_files(process_directory)
    total_delete = process_result["delete"] + remove_result["delete"]

    combined_result = {
        "copy": process_result["copy"],
        "upload": process_result["upload"],
        "delete": total_delete,
    }
    print(combined_result)


if __name__ == "__main__":
    main()
