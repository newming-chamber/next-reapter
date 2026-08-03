from module.config import env
from module.ftp_sync import FTPManager
from module.file_utils import FileManager
from module.logger import LoggerSetup


def main():
    try:
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
        # 현재는 이미지(.jpg)만 회수한다.
        # XML 백업 회수는 누적 규모를 확인한 뒤 별도로 결정한다.
        remove_result = file_manager.remove_old_files(extensions=(".jpg",))

        combined_result = {
            "upload": len(process_result),
            "delete": len(remove_result),
        }
        if press_name in need_sync_press:
            combined_result["download"] = len(download_result)

        print(combined_result)
    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    main()
