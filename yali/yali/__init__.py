

__version__ = "0.1"


def default_runner():
    import yali.gui.runner
    return runner.Runner()
