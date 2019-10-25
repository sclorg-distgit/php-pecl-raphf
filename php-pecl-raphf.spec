# centos/sclo spec file for php-pecl-raphf, from:
#
# remirepo spec file for php-pecl-raphf
# with SCL compatibility, from:
#
# Fedora spec file for php-pecl-raphf
#
# Copyright (c) 2013-2019 Remi Collet
# License: CC-BY-SA
# http://creativecommons.org/licenses/by-sa/4.0/
#
# Please, preserve the changelog entries
#
%if 0%{?scl:1}
%global sub_prefix sclo-%{scl_prefix}
%if "%{scl}" == "rh-php70"
%global sub_prefix sclo-php70-
%endif
%if "%{scl}" == "rh-php71"
%global sub_prefix sclo-php71-
%endif
%if "%{scl}" == "rh-php72"
%global sub_prefix sclo-php72-
%endif
%if "%{scl}" == "rh-php73"
%global sub_prefix sclo-php73-
%endif
%scl_package        php-pecl-raphf
%endif

%global pecl_name  raphf
# tests disabled because of circular dependency on pecl/http
# tests requires pecl/http 2.0.0
%global with_tests %{?_with_tests:1}%{!?_with_tests:0}
%global ini_name  40-%{pecl_name}.ini

Summary:        Resource and persistent handles factory
Name:           %{?sub_prefix}php-pecl-%{pecl_name}
Version:        2.0.1
Release:        1%{?dist}
License:        BSD
Group:          Development/Languages
URL:            http://pecl.php.net/package/%{pecl_name}
Source0:        http://pecl.php.net/get/%{pecl_name}-%{version}%{?prever}.tgz

BuildRequires:  %{?scl_prefix}php-devel > 7
BuildRequires:  %{?scl_prefix}php-pear
%if %{with_tests}
BuildRequires:  %{?scl_prefix}php-pecl-http >= 2.0.0
%endif

Requires:       %{?scl_prefix}php(zend-abi) = %{php_zend_api}
Requires:       %{?scl_prefix}php(api) = %{php_core_api}

Provides:       %{?scl_prefix}php-%{pecl_name} = %{version}
Provides:       %{?scl_prefix}php-%{pecl_name}%{?_isa} = %{version}
Provides:       %{?scl_prefix}php-pecl-%{pecl_name} = %{version}-%{release}
Provides:       %{?scl_prefix}php-pecl-%{pecl_name}%{?_isa} = %{version}-%{release}
Provides:       %{?scl_prefix}php-pecl(%{pecl_name}) = %{version}
Provides:       %{?scl_prefix}php-pecl(%{pecl_name})%{?_isa} = %{version}

%if 0%{?fedora} < 20 && 0%{?rhel} < 7
# Filter shared private
%{?filter_provides_in: %filter_provides_in %{_libdir}/.*\.so$}
%{?filter_setup}
%endif


%description
A reusable split-off of pecl_http's persistent handle and resource
factory API.

Package built for PHP %(%{__php} -r 'echo PHP_MAJOR_VERSION.".".PHP_MINOR_VERSION;')%{?scl: as Software Collection (%{scl} by %{?scl_vendor}%{!?scl_vendor:rh})}.


%package devel
Summary:       %{name} developer files (header)
Group:         Development/Libraries
Requires:      %{name}%{?_isa} = %{version}-%{release}
Requires:      %{?scl_prefix}php-devel%{?_isa}
Provides:      %{?scl_prefix}php-pecl-%{pecl_name}-devel = %{version}-%{release}
Provides:      %{?scl_prefix}php-pecl-%{pecl_name}-devel%{?_isa} = %{version}-%{release}

%description devel
These are the files needed to compile programs using %{name}.


%prep
%setup -q -c
mv %{pecl_name}-%{version}%{?prever} NTS

cd NTS
# Sanity check, really often broken
extver=$(sed -n '/#define PHP_RAPHF_VERSION/{s/.* "//;s/".*$//;p}' php_raphf.h)
if test "x${extver}" != "x%{version}%{?prever}"; then
   : Error: Upstream extension version is ${extver}, expecting %{version}%{?prever}.
   exit 1
fi
cd ..

# Create configuration file
cat << 'EOF' | tee %{ini_name}
; Enable %{pecl_name} extension module
extension=%{pecl_name}.so

; Configuration
;raphf.persistent_handle.limit = -1
EOF


%build
cd NTS
%{_bindir}/phpize
%configure \
    --with-php-config=%{_bindir}/php-config
make %{?_smp_mflags}


%install
make -C NTS \
     install INSTALL_ROOT=%{buildroot}

# install config file
install -D -m 644 %{ini_name} %{buildroot}%{php_inidir}/%{ini_name}

# Install XML package description
install -D -m 644 package.xml %{buildroot}%{pecl_xmldir}/%{name}.xml

# Test & Documentation
for i in $(grep 'role="test"' package.xml | sed -e 's/^.*name="//;s/".*$//')
do install -Dpm 644 NTS/$i %{buildroot}%{pecl_testdir}/%{pecl_name}/$i
done
for i in $(grep 'role="doc"' package.xml | sed -e 's/^.*name="//;s/".*$//')
do install -Dpm 644 NTS/$i %{buildroot}%{pecl_docdir}/%{pecl_name}/$i
done


# when pear installed alone, after us
%triggerin -- %{?scl_prefix}php-pear
if [ -x %{__pecl} ] ; then
    %{pecl_install} %{pecl_xmldir}/%{name}.xml >/dev/null || :
fi

# posttrans as pear can be installed after us
%posttrans
if [ -x %{__pecl} ] ; then
    %{pecl_install} %{pecl_xmldir}/%{name}.xml >/dev/null || :
fi

%postun
if [ $1 -eq 0 -a -x %{__pecl} ] ; then
    %{pecl_uninstall} %{pecl_name} >/dev/null || :
fi


%check
cd NTS
: Minimal load test for NTS extension
%{__php} --no-php-ini \
    --define extension=modules/%{pecl_name}.so \
    --modules | grep %{pecl_name}

%if %{with_tests}
for mod in json hash iconv propro; do
  if [ -f %{php_extdir}/${mod}.so ]; then
    modules="$modules -d extension=${mod}.so"
  fi
done

: Upstream test suite for NTS extension
TEST_PHP_EXECUTABLE=%{__php} \
TEST_PHP_ARGS="-n $modules -d extension=$PWD/modules/%{pecl_name}.so -d extension=http.so" \
NO_INTERACTION=1 \
REPORT_EXIT_STATUS=1 \
%{__php} -n run-tests.php
%endif


%files
%doc %{pecl_docdir}/%{pecl_name}
%{pecl_xmldir}/%{name}.xml
%config(noreplace) %{php_inidir}/%{ini_name}
%{php_extdir}/%{pecl_name}.so

%files devel
%doc %{pecl_testdir}/%{pecl_name}
%{php_incldir}/ext/%{pecl_name}


%changelog
* Fri Oct 25 2019 Remi Collet <remi@remirepo.net> - 2.0.1-1
- update to 2.0.1

* Thu Nov 15 2018 Remi Collet <remi@remirepo.net> - 2.0.0-3
- build for sclo-php72

* Wed Aug  9 2017 Remi Collet <remi@fedoraproject.org> - 2.0.0-2
- minor change for sclo-php71

* Thu Nov  3 2016 Remi Collet <remi@fedoraproject.org> - 2.0.0-1
- update to 2.0.0 for PHP 7

* Tue Jan 19 2016 Remi Collet <remi@fedoraproject.org> - 1.1.2-1
- cleanup for SCLo build

* Tue Jan 19 2016 Remi Collet <remi@fedoraproject.org> - 1.1.2-1
- Update to 1.1.2 (stable)

* Mon Dec  7 2015 Remi Collet <remi@fedoraproject.org> - 1.1.1-0.1.RC1
- Update to 1.1.1RC1 (beta)

* Tue Jul 28 2015 Remi Collet <remi@fedoraproject.org> - 1.1.0-1
- Update to 1.1.0 (stable)

* Sun Jun 21 2015 Remi Collet <remi@fedoraproject.org> - 1.0.4-5
- allow build against rh-php56 (as more-php56)
- drop runtime dependency on pear, new scriptlets

* Wed Dec 24 2014 Remi Collet <remi@fedoraproject.org> - 1.0.4-4.1
- Fedora 21 SCL mass rebuild

* Mon Aug 25 2014 Remi Collet <rcollet@redhat.com> - 1.0.4-4
- improve SCL build

* Wed Apr  9 2014 Remi Collet <remi@fedoraproject.org> - 1.0.4-3
- add numerical prefix to extension configuration file

* Tue Mar 18 2014 Remi Collet <rcollet@redhat.com> - 1.0.4-2
- adapt for SCL

* Tue Nov 26 2013 Remi Collet <remi@fedoraproject.org> - 1.0.4-1
- Update to 1.0.4 (stable)

* Fri Nov 15 2013 Remi Collet <remi@fedoraproject.org> - 1.0.3-1
- Update to 1.0.3 (stable)
- install doc in pecl doc_dir
- install tests in pecl test_dir
- add --with tests option (not enabled, need pecl/http)

* Tue Aug 20 2013 Remi Collet <remi@fedoraproject.org> - 1.0.2-1
- Update to 1.0.2 (stable)

* Tue Aug 20 2013 Remi Collet <remi@fedoraproject.org> - 1.0.1-1
- Update to 1.0.1 (stable)

* Tue Aug 20 2013 Remi Collet <remi@fedoraproject.org> - 1.0.0-1
- Update to 1.0.0 (stable)

* Sun Jun 16 2013 Remi Collet <remi@fedoraproject.org> - 0.1.0-1
- initial package, version 0.1.0 (beta)
