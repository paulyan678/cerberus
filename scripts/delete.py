from _bootstrap import bootstrap

bootstrap()

from cerberus.cli import delete_files_main  # noqa: E402

if __name__ == "__main__":
    delete_files_main()
