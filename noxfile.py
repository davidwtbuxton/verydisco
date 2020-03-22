import nox


@nox.session(python=["3.7", "3.8"])
def tests(session):
    session.install("pytest")
    session.install(".")
    session.run("pytest")


@nox.session
def lint(session):
    session.install("yapf")
    session.run('yapf', '--diff', '--recursive', 'src', 'tests')
