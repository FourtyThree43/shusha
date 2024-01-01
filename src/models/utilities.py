class HelperUtilities:

    @staticmethod
    def sizeof_fmt(num, delim=" ", suffix="B"):
        for unit in ("", "K", "M", "G", "T", "P", "E", "Z"):
            if abs(num) < 1024.0:
                return f"{num:3.1f}{delim}{unit}{suffix}"
            num /= 1024.0
        return f"{num:.1f}{delim}Yi{suffix}"
