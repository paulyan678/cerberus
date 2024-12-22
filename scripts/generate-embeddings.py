from _bootstrap import bootstrap

bootstrap()

from cerberus.cli import embed_main  # noqa: E402

if __name__ == "__main__":
    embed_main()
