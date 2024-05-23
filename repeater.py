import os
from module.config import env
from module.ftp_sync import FTPManager
from module.file_utils import FileManager
from module.logger import LoggerSetup


def main():
    press_name = env["PRESS_NAME"]
    logger_setup = LoggerSetup(press_name)
    logger = logger_setup.logger
    logger.info(f"Start {press_name} Repeater")

    file_manager = FileManager(press_name)

    download_result = []
    need_sync_press = ["mk", "fn"]
    if press_name in need_sync_press:
        ftp_manager = FTPManager(press_name, file_manager)
        download_result = ftp_manager.sync_press()

    process_result = file_manager.process_files()
    # process_directory = os.path.join(os.getcwd(), "origin_files")
    # remove_result = file_manager.remove_old_files(process_directory)

    combined_result = {
        "upload": len(process_result),
        # "delete": len(remove_result),
    }
    if press_name in need_sync_press:
        combined_result["download"] = len(download_result)

    print(combined_result)


if __name__ == "__main__":
    main()
