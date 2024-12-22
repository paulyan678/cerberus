from _bootstrap import bootstrap

bootstrap()

from cerberus.cli import confusion_main  # noqa: E402

if __name__ == "__main__":
    confusion_main()
