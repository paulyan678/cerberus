from _bootstrap import bootstrap

bootstrap()

from cerberus.cli import list_files_main  # noqa: E402

if __name__ == "__main__":
    list_files_main()
