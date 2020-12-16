rpmbuild_src = $(shell rpmbuild --eval '%{_sourcedir}')

.PHONY: prepare
prepare:
	dnf -y install rpmdevtools rpm-build
	cp *.* $(rpmbuild_src)
	spectool -g -R $(spec)

.PHONY: srpm
srpm: prepare
	rpmbuild -bs --define "_srcrpmdir $(outdir)" $(spec)

.PHONY: rpm
rpm: prepare
	rpmbuild -bb --define "_rpmdir $(outdir)" $(spec)
