# This repository's OWN toolchain, and the only one it has. Every command the
# orchestrator runs against it is DECLARED in .livespec.jsonc and invoked
# verbatim -- the check suite, the bootstrap recipe, and the two conformance
# premises this repository chose to answer with a command of its own.
#
# Nothing this fleet ships is installed here, and no recipe of the fleet's
# naming convention exists, which is the property the adopter leg of every
# dispatch-path seam test asserts.

verify:
	python3 -m unittest discover

install-hooks:
	cp hooks/pre-commit .git/hooks/pre-commit
	cp hooks/red-green-replay-gate .git/hooks/red-green-replay-gate
	chmod +x .git/hooks/pre-commit .git/hooks/red-green-replay-gate

verify-hooks:
	test -x .git/hooks/pre-commit

.PHONY: verify install-hooks verify-hooks
