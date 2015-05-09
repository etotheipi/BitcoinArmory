Name:     armory
Version:  0.93.1
Release:  1%{?dist}
Summary:  Advanced Bitcoin Wallet Management Software
License:  AGPLv3
URL:      https://bitcoinarmory.com
Source0:  https://github.com/etotheipi/BitcoinArmory/archive/v0.93.1.tar.gz

%description
Armory is advanced program for managing multiple Bitcoin wallets with the
highest level of security available.  Use top-of-the-line wallet encryption,
print permanent paper backups of your wallets, and store your Bitcoins on
an offline computer for maximum security from online threats.  Armory is
open-source software licensed under the AGPLv3.

%prep
%autosetup -n BitcoinArmory-0.93.1

%build
make %{?_smp_mflags}

%install
%make_install

%files
/usr/share/armory/*
/usr/lib/armory/*
/usr/bin/armory
/usr/share/applications/armory*

%changelog
* Thu Jul 07 2011 John Smith <john@example.com> - 0.93.1-1
- Initial RPM release
