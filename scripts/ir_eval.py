from _bootstrap import bootstrap

bootstrap()

from cerberus.cli import ir_eval_main  # noqa: E402

if __name__ == "__main__":
    ir_eval_main()
