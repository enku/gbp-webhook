"""noxfile for ci/cd testing"""

# pylint: disable=missing-docstring
import nox


@nox.session(python=("3.12", "3.13", "3.14"))
@nox.parametrize("gbpcli", ["stable", "scm"])
def tests(session: nox.Session, gbpcli: str) -> None:
    session.install(".")
    dev_dependencies = nox.project.load_toml("pyproject.toml")["dependency-groups"][
        "dev"
    ]
    session.install(*dev_dependencies)

    if gbpcli == "scm":
        session.install("-U", "git+https://github.com/enku/gbpcli.git")

    session.run("coverage", "run", "-m", "tests")
    session.run("coverage", "report")
