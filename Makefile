SLYP_VERSION=$(shell grep '^version = ' pyproject.toml | cut -d '"' -f2)

.PHONY: release
release:
	git tag -s "$(SLYP_VERSION)" -m "v$(SLYP_VERSION)"
	-git push $(shell git rev-parse --abbrev-ref @{push} | cut -d '/' -f1) refs/tags/$(SLYP_VERSION)
