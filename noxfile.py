"""noxfile for ci/cd testing"""
# pylint: disable=missing-docstring
import nox


@nox.session(python=("3.12", "3.13", "3.14"))
@nox.parametrize("gbpcli", ["stable", "scm"])
def tests(session: nox.Session, gbpcli: str) -> None:
    session.install(".", "coverage")

    if gbpcli == "scm":
        session.install("-U", "git+https://github.com/enku/gbpcli.git")

    session.run("coverage", "run", "-m", "tests")
    session.run("coverage", "report")
