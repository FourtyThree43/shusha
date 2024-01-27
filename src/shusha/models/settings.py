from shusha.models.utilities import load_configuration  # , save_configuration


class AppSettings:

    def __init__(self):
        self.config_dict = load_configuration()

    def get_aria2_config(self):
        return self.config_dict.get("USER", {}).get("aria2", {})

    def get_aria2_options(self):
        return self.config_dict.get("USER", {}).get("aria2.options", {})

    def get_aria2_http_options(self):
        return self.config_dict.get("USER", {}).get("aria2.options.http", {})

    def get_download_dir(self):
        return self.config_dict.get("USER", {}).get("download_dir", "")

    def set_download_dir(self, download_dir):
        self.config_dict["USER"]["download_dir"] = download_dir
        # save_configuration(self.config_dict)

    def get_logs_dir(self):
        return self.config_dict.get("USER", {}).get("logs_dir", "")

    def set_logs_dir(self, logs_dir):
        self.config_dict["USER"]["logs_dir"] = logs_dir
        # save_configuration(self.config_dict)

    def update_settings(self, settings_dict):
        self.config_dict["USER"].update(settings_dict)
        # save_configuration(self.config_dict)

    def save_settings(self):
        # save_configuration(self.config_dict)
        pass


if __name__ == "__main__":
    settings = AppSettings()

    # Example: Get and set download directory
    download_dir = settings.get_download_dir()
    print("Current Download Directory:", download_dir)

    new_download_dir = "/path/to/new/download/directory"
    settings.set_download_dir(new_download_dir)
    print("Updated Download Directory:", settings.get_download_dir())

    # Example: Get and set logs directory
    logs_dir = settings.get_logs_dir()
    print("Current Logs Directory:", logs_dir)

    new_logs_dir = "/path/to/new/logs/directory"
    settings.set_logs_dir(new_logs_dir)
    print("Updated Logs Directory:", settings.get_logs_dir())

    # Example: Update and save general settings
    update_dict = {"new_setting": "new_value"}
    settings.update_settings(update_dict)
    print("Updated Settings:", settings.config_dict.get("USER", {}))

    settings.save_settings()
