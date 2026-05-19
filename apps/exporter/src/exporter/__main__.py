from exporter.collector import LogCollector


def run():
    file_path = "/var/log/syslog"
    collector = LogCollector(file_path)
    collector.start()


if __name__ == "__main__":
    run()
