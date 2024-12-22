from _bootstrap import bootstrap

bootstrap()

from cerberus.cli import upload_main  # noqa: E402

if __name__ == "__main__":
    upload_main()
