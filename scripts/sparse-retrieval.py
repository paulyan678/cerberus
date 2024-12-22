from _bootstrap import bootstrap

bootstrap()

from cerberus.cli import sparse_main  # noqa: E402

if __name__ == "__main__":
    sparse_main()
