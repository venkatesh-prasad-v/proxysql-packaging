%define        __spec_install_post %{nil}
%define          debug_package %{nil}
%define        __os_install_post %{_dbpath}/brp-compress

%{!?with_systemd:%global systemd 0}
%{?el7:          %global systemd 1}
%{?el8:          %global systemd 1}

Summary: A high-performance MySQL proxy
Name: proxysql2
Version: @@VERSION@@
Release: @@RELEASE@@
License: GPL+
Group: Development/Tools
Source0 : proxysql2-%{version}.tar.gz
Source1 : proxysql-admin
Source2 : proxysql-admin.cnf
Source5 : LICENSE
Source6 : proxysql-logrotate
Source7 : proxysql-status
URL: http://www.proxysql.com/
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
Requires: logrotate
Requires(pre): shadow-utils
Requires(pre): /usr/sbin/useradd, /usr/bin/getent
Requires(postun): /usr/sbin/userdel
%if 0%{?systemd}
BuildRequires:  systemd
BuildRequires:  pkgconfig(systemd)
Requires(post):   systemd
Requires(preun):  systemd
Requires(postun): systemd
%else
Requires(post):   /sbin/chkconfig
Requires(preun):  /sbin/chkconfig
Requires(preun):  /sbin/service
%endif


%description
%{summary}

%prep
%setup -q
install %SOURCE5 %{name}-%{version}

%build
sed -i -e 's/c++11/c++0x/' lib/Makefile
sed -i -e 's/c++11/c++0x/' src/Makefile
make clean
make

%install
install -d %{buildroot}/%{_bindir}
install -d  %{buildroot}/%{_sysconfdir}
install -d  %{buildroot}/%{_sysconfdir}/init.d
install -d  %{buildroot}/%{_sysconfdir}/logrotate.d
install -m 0755 src/proxysql %{buildroot}/%{_bindir}
install -m 0640 etc/proxysql.cnf %{buildroot}/%{_sysconfdir}
install -m 0640 %SOURCE2 %{buildroot}/%{_sysconfdir}
%if 0%{?systemd}
  install -m 0755 -d %{buildroot}/%{_unitdir}
  install -m 0755 systemd/system/proxysql.service %{buildroot}/%{_unitdir}/proxysql.service
%else
  install -m 0755 -d %{buildroot}/etc/rc.d/init.d
  install -m 0755 etc/init.d/proxysql %{buildroot}/%{_sysconfdir}/init.d
%endif

install -d %{buildroot}/var/lib/proxysql
install -d %{buildroot}/var/run/proxysql
install -m 0775 %SOURCE1 %{buildroot}/%{_bindir}/proxysql-admin
install -m 0775 tools/proxysql_galera_checker.sh %{buildroot}/%{_bindir}/proxysql_galera_checker
install -m 0775 tools/proxysql_galera_writer.pl %{buildroot}/%{_bindir}/proxysql_galera_writer
install -m 0775 %SOURCE7 %{buildroot}/%{_bindir}/proxysql-status
install -m 0644 etc/logrotate.d/proxysql %{buildroot}%{_sysconfdir}/logrotate.d/proxysql-logrotate

%clean
rm -rf %{buildroot}


%pre
getent group proxysql >/dev/null || groupadd -r proxysql
useradd -r -g proxysql -r -d /var/lib/proxysql -s /bin/false \
    -c "ProxySQL" proxysql >/dev/null 2>&1 || :

STATUS_FILE=/tmp/PROXYSQL_UPGRADE_MARKER
EXIST=$(ps wwaux | grep /usr/bin/proxysql | grep -v grep | wc -l )
if [ "$EXIST" -gt "0" ]; then
    echo "SERVER_TO_START=1" >> $STATUS_FILE
else
    echo "SERVER_TO_START=0" >> $STATUS_FILE
fi



%post

case "$1" in
    1)
        %if 0%{?systemd}
            %systemd_post proxysql.service
            if [ $1 == 1 ]; then
                /usr/bin/systemctl enable proxysql >/dev/null 2>&1 || :
            fi
        %else
            if [ $1 == 1 ]; then
                /sbin/chkconfig --add proxysql
            fi
        %endif
    ;;
esac
exit 0

%postun
%if 0%{?systemd}
  %systemd_postun_with_restart proxysql.service
%else
  if [ $1 -ge 1 ]; then
    /sbin/service proxysql restart >/dev/null 2>&1 || :
  fi
%endif
exit 0

%preun
if [ "$1" = "0" ]; then
%if 0%{?systemd}
    /bin/systemctl disable proxysql.service >/dev/null 2>&1 || :
    /bin/systemctl stop proxysql.service > /dev/null 2>&1 || :
%else
    /sbin/service proxysql stop >/dev/null 2>&1 || :
    /sbin/chkconfig --del proxysql
%endif
fi
exit 0

%files
%defattr(-,root,root,-)
%{_bindir}/proxysql_galera_checker
%{_bindir}/proxysql_galera_writer
%{_bindir}/proxysql-admin
%{_bindir}/proxysql-status
%config(noreplace) %{_sysconfdir}/logrotate.d/proxysql-logrotate
%defattr(-,proxysql,proxysql,-)
%{_bindir}/proxysql
%if 0%{?systemd}
%{_unitdir}/proxysql.service
%else
%{_sysconfdir}/init.d/proxysql
%endif
/var/lib/proxysql
/var/run/proxysql
%defattr(-,root,proxysql,-)
%config(noreplace) %{_sysconfdir}/proxysql.cnf
%config(noreplace) %{_sysconfdir}/proxysql-admin.cnf
%doc LICENSE

%changelog
* Tue Aug 09 2017  Evgeniy Patlan <evgeniy.patlan@percona.com> 1.3.9-1.1
- added proxysql-logrotate

* Wed Sep 21 2016  Evgeniy Patlan <evgeniy.patlan@percona.com> 1.2.3-1.0.1
- added proxysql-admin tool

* Fri Jul 15 2016  Evgeniy Patlan <evgeniy.patlan@percona.com> 1.2.0-1.0.1
- First build of proxysql for Percona.
