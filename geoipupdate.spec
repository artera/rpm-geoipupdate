%undefine _missing_build_ids_terminate_build
%global debug_package %{nil}
%global gopath %{_datadir}/gocode
%global gobuilddir %{_builddir}/_build

# https://github.com/maxmind/geoipupdate
%global goipath	github.com/maxmind/geoipupdate

Name:    geoipupdate
Version: 4.9.0
Release: 1%{?dist}
Summary: Update GeoIP2 binary databases from MaxMind

License: ASL 2.0 or MIT
URL:     https://dev.maxmind.com/geoip/geoipupdate/
Source0: https://github.com/maxmind/geoipupdate/archive/v%{version}/%{name}-%{version}.tar.gz
Source1: geoipupdate.service
Source2: geoipupdate.timer

BuildRequires: systemd-rpm-macros
BuildRequires: golang
BuildRequires: coreutils
BuildRequires: make
BuildRequires: pandoc
BuildRequires: perl-interpreter
BuildRequires: perl(File::Temp)
BuildRequires: perl(strict)
BuildRequires: perl(warnings)
BuildRequires: sed
# Legacy databases fetched by cron6 sub-package no longer available
Obsoletes: geoipupdate-cron < %{version}-%{release}
Obsoletes: geoipupdate-cron6 < %{version}-%{release}

%description
The GeoIP Update program performs automatic updates of GeoIP2 binary databases.

%prep
%setup
mkdir -p %{gobuilddir}/src/$(dirname %{goipath})
ln -s $(pwd) %{gobuilddir}/src/%{goipath}
export GOPATH="%{gobuilddir}:${GOPATH:+${GOPATH}:}%{?gopath}"

%build
cd %{gobuilddir}/src/%{goipath}/cmd/geoipupdate
go build \
    -trimpath \
    -buildmode=pie \
    -mod=readonly \
    -modcacherw \
    -ldflags "-extldflags \"$LDFLAGS\" -X main.defaultConfigFile=%{_sysconfdir}/GeoIP.conf -X main.defaultDatabaseDirectory=%{_datadir}/GeoIP -X main.version=%{version}" \
    -o "%{gobuilddir}/bin/geoipupdate" \
    .

cd %{gobuilddir}/src/%{goipath}
# Work around hardcoded "build" path in dev-bin/make-man-pages.pl
ln -s %{gobuilddir} build

# Prepare the config files and documentation
make BUILDDIR=%{gobuilddir} CONFFILE=%{_sysconfdir}/GeoIP.conf DATADIR=%{_datadir}/GeoIP data

%install
# Install the geoipupdate program
install -d %{buildroot}%{_bindir}
install -p -m 0755 %{gobuilddir}/bin/geoipupdate %{buildroot}%{_bindir}/geoipupdate

# Install the configuration file
# By default we just use the free GeoIP2 databases
install -d %{buildroot}%{_sysconfdir}
install -p -m 0644 conf/GeoIP.conf.default %{buildroot}%{_sysconfdir}/GeoIP.conf

# Ensure the GeoIP data directory exists
# Note: not using %%ghost files for default databases to avoid issues when co-existing with the geolite2 package
install -d %{buildroot}%{_datadir}/GeoIP

# Install systemd units
install -Dm0644 %{SOURCE1} %{buildroot}%{_unitdir}/geoipupdate.service
install -Dm0644 %{SOURCE2} %{buildroot}%{_unitdir}/geoipupdate.timer

# Install the manpages
install -d %{buildroot}%{_mandir}/man1
install -p -m 0644 %{gobuilddir}/geoipupdate.1 %{buildroot}%{_mandir}/man1/geoipupdate.1
install -d %{buildroot}%{_mandir}/man5
install -p -m 0644 %{gobuilddir}/GeoIP.conf.5 %{buildroot}%{_mandir}/man5/GeoIP.conf.5

%files
%license LICENSE-APACHE LICENSE-MIT
%doc conf/GeoIP.conf.default README.md CHANGELOG.md
%doc doc/GeoIP.conf.md doc/geoipupdate.md
%config(noreplace) %{_sysconfdir}/GeoIP.conf
%{_bindir}/geoipupdate
%dir %{_datadir}/GeoIP/
%{_mandir}/man1/geoipupdate.1*
%{_mandir}/man5/GeoIP.conf.5*
%{_unitdir}/geoipupdate.service
%{_unitdir}/geoipupdate.timer

%post
%systemd_post geoipupdate.timer

%preun
%systemd_preun geoipupdate.timer

%postun
%systemd_postun_with_restart geoipupdate.timer
